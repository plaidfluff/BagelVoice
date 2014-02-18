from peewee import *

database = SqliteDatabase('db/voicebox.db')
database.connect()

# Run inside a transaction
def transaction():
    return database.transaction()

class BaseModel(Model):
    class Meta:
        database = database

    @staticmethod
    def update_schema():
        ''' do nothing by default '''

# A user, with a 1:1 mapping to a Twilio account
class User(BaseModel):
    username = CharField(null=False,unique=True)
    password = CharField()
    email = CharField(unique=True)
    twilio_sid = CharField(unique=True)
    twilio_auth_token = CharField()
    timezone = CharField(default='UTC')

# Notification settings
class Notification(BaseModel):
    user = ForeignKeyField(User, related_name='notifications')
    # notification URI, e.g. mailto:foo@example.com, xmpp:foo@example.com, or aim:aolsystemmsg
    uri = CharField()
    # Notify on an incoming SMS
    notify_sms = BooleanField(default=False)
    # Notify when a call is received
    notify_call = BooleanField(default=False)
    # Notify when a voicemail is received
    notify_voicemail = BooleanField(default=True)

# User login sessions
class WebSession(BaseModel):
    session_id = CharField(unique=True)
    user = ForeignKeyField(User, related_name='web_sessions')
    last_ip = CharField()
    last_seen = DateTimeField()

# An inbox, i.e. a phone number
class Inbox(BaseModel):
    user = ForeignKeyField(User, related_name='inboxes')
    phone_number = CharField(unique=True)
    name = CharField()
    voicemail_greeting = CharField(null=True)

# Routes for a call to take
class CallRoute(BaseModel):
    inbox = ForeignKeyField(Inbox, related_name='routes')
    name = CharField();
    
    max_ring_time = IntegerField(null=True)
    # destination type; must be something supported by TwiML (e.g. Number, Sip)
    dest_type = CharField()
    dest_addr = CharField()
    active = BooleanField(default=True)

    class Meta:
        indexes = (
            (('inbox', 'dest_type', 'dest_addr'), True),
            )

# When to activate a call route
class CallRouteRule(BaseModel):
    route = ForeignKeyField(CallRoute, related_name='rules')
    # start time (in user's local timezone)
    start_time = TimeField()
    # end time (in user's local timezone); if end_time < start_time then this inverts the rule (i.e. only OUTSIDE this period)
    end_time = TimeField()
    # on which days to activate (string containing one or more of MTWRFSU)
    active_days = CharField()

# Someone with whom a conversation occurs
class Associate(BaseModel):
    user = ForeignKeyField(User, related_name='phonebook')
    display_name = CharField(null=True)
    phone_number = CharField()
    blocked = BooleanField(default=False)
    from_city = CharField(null=True)
    from_state = CharField(null=True)
    from_zip = CharField(null=True)
    from_country = CharField(null=True)

    class Meta:
        indexes = (
            # ensure that any given phone number only appears once
            (('user', 'phone_number'), True),
            )
    
# A conversation thread
class Conversation(BaseModel):
    user = ForeignKeyField(User, related_name='threads')
    inbox = ForeignKeyField(Inbox, related_name='threads')
    associate = ForeignKeyField(Associate, related_name='threads')
    last_update = DateTimeField(index=True)
    unread = BooleanField(default=True)
    class Meta:
        indexes = (
            (('last_update','inbox','associate'),False),
            (('last_update','user','associate'),False),
            )
        order_by = ('-last_update',)    

# An event in a conversation
class Event(BaseModel):
    sid = CharField(unique=True)
    inbox = ForeignKeyField(Inbox, related_name='events')
    conversation = ForeignKeyField(Conversation, related_name='events')
    type = CharField()
    time = DateTimeField()
    last_update = DateTimeField()
    inbound = BooleanField()
    call_duration = IntegerField(null=True)
    message_body = CharField(null=True)
    status = CharField(null=True)
    caller_id_string = CharField(null=True)
    class Meta:
        order_by = ('-time',)
    
class Attachment(BaseModel):
    sid = CharField(unique=True)
    duration = IntegerField(null=True)
    url = CharField()
    mime_type = CharField()
    event = ForeignKeyField(Event, related_name='media')
    msg_new = BooleanField(default=True)

def create_tables():
    for table in [
        User,
        Notification,
        WebSession,
        Inbox,
        CallRoute,
        CallRouteRule,
        Associate,
        Conversation,
        Event,
        Attachment
        ]:
        table.create_table(fail_silently=True)
        table.update_schema()


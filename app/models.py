import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator, CHAR, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.sqlite import JSON

db = SQLAlchemy()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class User(db.Model):
    """
    rate: [1, 2, 3, 4, 5]
    posts: [
        {
            "postid": "postid",
            "sender": "uuid", 
            "timestamp": "datetime",
            "content": "string",
            "icon": "string",
            "responses": [
                {
                    "postid": "postid",
                    "sender": "uuid",
                    "timestamp": "datetime",
                    "icon": "string",
                    "content": "string"
                },
                {
                    "postid": "postid",
                    "sender": "uuid",
                    "timestamp": "datetime",
                    "icon": "string",
                    "content": "string"
                }
            ]
        },
    ]
    queries: [
        {
            "sender": "uuid", 
            "content": [
                {
                    "sender": "uuid1",
                    "content": "string"
                },
                {
                    "sender": "uuid2",
                    "content": "string"
                },
            ]
        }
    ]
    """
    id             = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    username       = db.Column(db.String, nullable=False, unique=True)
    password       = db.Column(db.String, nullable=False)
    admin          = db.Column(db.Boolean, nullable=False, default=False)
    settings       = db.Column(JSON, nullable=True)
    current        = db.Column(db.Integer, nullable=False, default=0)  # money
    rate           = db.Column(JSON, nullable=True)
    posts          = db.Column(JSON, nullable=True)
    queries       = db.Column(JSON, nullable=True)
    credit         = db.Column(JSON, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Bot(db.Model):
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    name           = db.Column(db.String, nullable=False, unique=True)
    url            = db.Column(db.String, nullable=False)
    base_model     = db.Column(db.String, nullable=False)
    quota          = db.Column(db.Integer, nullable=True)
    price          = db.Column(db.Integer, nullable=False)
    prompts        = db.Column(JSON, nullable=True)
    icon           = db.Column(db.String, nullable=False)
    knowledge_base = db.Column(db.String, nullable=True)
    is_default     = db.Column(db.Boolean, nullable=False, default=False)
    rate           = db.Column(JSON, nullable=True)

    def __repr__(self):
        return f'<Bot {self.base_model}>'


class Session(db.Model):
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    token          = db.Column(db.Text, nullable=False)
    expiry         = db.Column(db.TIMESTAMP, nullable=False)
    # foreign key
    user           = db.relationship('User', backref=db.backref('session', lazy=True))

    def __repr__(self):
        return f'<Session {self.token}>'


class Chat(db.Model):
    id             = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id        = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    title          = db.Column(db.String, nullable=False)
    settings       = db.Column(db.JSON, nullable=True)
    history        = db.Column(db.JSON, nullable=False)
    # foreign key
    user           = db.relationship('User', backref=db.backref('chat', lazy=True))

    def __repr__(self):
        return f'<Chat {self.id}>'


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    user_name = db.Column(db.String, nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    content = db.Column(db.String, nullable=True)
    score = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f'<content {self.content}>'


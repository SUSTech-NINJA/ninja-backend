import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.sqlite import JSON

db = SQLAlchemy()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR

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
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    settings = db.Column(JSON, nullable=True)
    current = db.Column(db.Integer, nullable=False, default=0)
    credit = db.Column(JSON, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)  # unique?
    url = db.Column(db.String, nullable=False)
    usage_limit = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    prompts = db.Column(JSON, nullable=False)


class Session(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    expiry = db.Column(db.TIMESTAMP, nullable=False)
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))


class Chat(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    settings = db.Column(db.JSON, nullable=False)
    history = db.Column(db.JSON, nullable=False)
    user = db.relationship('User', backref=db.backref('chats', lazy=True))

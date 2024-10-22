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
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    admin = db.Column()
    settings = db.Column(JSON, nullable=True)
    current = db.Column(db.Integer, nullable=False, default=0)  # money
    comments = db.Column(JSON, nullable=True)
    posts = db.Column(JSON, nullable=True)
    queries = db.Column(JSON, nullable=True)
    credit = db.Column(JSON, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String, nullable=False, unique=True)
    url = db.Column(db.String, nullable=False)
    base_model = db.Column(db.String,nullable=False)
    quota = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Integer, nullable=False)
    prompts = db.Column(JSON, nullable=False)
    icon = db.Column(db.String, nullable=False)
    knowledge_base = db.Column(db.String, nullable=True)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    expiry = db.Column(db.TIMESTAMP, nullable=False)

    user = db.relationship('User', backref=db.backref('session', lazy=True))

    def __repr__(self):
        return f'<Session {self.token}>'


class Chat(db.Model):
    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    settings = db.Column(db.JSON, nullable=True)
    history = db.Column(db.JSON, nullable=False)

    user = db.relationship('User', backref=db.backref('chat', lazy=True))

    def __repr__(self):
        return f'<Chat {self.id}>'

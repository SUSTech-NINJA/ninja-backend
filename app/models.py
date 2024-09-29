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

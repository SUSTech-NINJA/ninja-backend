import os
import jwt
from uuid import uuid4
from app.models import db, User, Session
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# Same as the filename
auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user is None:
        return jsonify({'token': 'User not found', 'userid': 'null'}), 401

    if not check_password_hash(user.password, password):
        return jsonify({'token': 'Incorrect password', 'userid': 'null'}), 401

    uuid = str(uuid4())
    payload = {
        'admin': False,
        'session_id': uuid
    }

    new_session = Session(user_id=user.id, token=uuid, expiry=datetime(2025, 1, 1))
    db.session.add(new_session)
    db.session.commit()

    token = jwt.encode(payload, os.getenv('SECRET'), algorithm='HS256')
    return jsonify({'token': token, 'userid': user.id}), 200


@auth.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user is not None:
        return jsonify({'msg': 'User already exists'}), 401

    new_user = User(username=username, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'msg': 'Register successfully'}), 200


def verify(token: str, userid: str) -> bool:
    """
    Verify the token and check if the user id is the same.

    :param token: JWT token, contains session_id(uuid) and admin(bool)
    :param userid: User ID
    :type token: str
    :type userid: str
    :return: True if the token is valid or its admin, False otherwise.
    :rtype: bool
    """
    try:
        payload = jwt.decode(token, os.getenv('SECRET'), algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

    session = Session.query.filter_by(token=payload['session_id']).first()

    if session is None or session.expiry < datetime.now():
        return False

    return str(session.user_id) == userid or payload['admin']


def get_user(token: str) -> User:
    """
    Get the user object from the token.

    :param token: JWT token, contains session_id(uuid) and admin(bool)
    :type token: str
    :return: User object if the token is valid, None otherwise.
    :rtype: User
    """
    try:
        payload = jwt.decode(token, os.getenv('SECRET'), algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    session = Session.query.filter_by(token=payload['session_id']).first()

    if session is None or session.expiry < datetime.now():
        return None

    return User.query.filter_by(id=session.user_id).first()


# Test route for anything you like, DON'T COMMIT THIS.
@auth.route('/auth/test', methods=['GET', 'POST'])
def test():
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        pass

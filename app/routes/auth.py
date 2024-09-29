import os
import jwt
from uuid import uuid4
from app.models import db, User
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

# Same as the filename
auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    code = 200
    token = None
    user = User.query.filter_by(username=username).first()

    if user is None:
        code = 401
        token = 'User not found'
    elif not check_password_hash(user.password, password):
        code = 401
        token = 'Incorrect password'
    else:
        uuid = str(uuid4())
        payload = {
            'admin': False,
            'session_id': uuid
        }
        # TODO: Update Session Database
        token = jwt.encode(payload, os.getenv('SECRET'), algorithm='HS256')

    return jsonify({'token': token, 'userid': user.id}), code


@auth.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    code = 200
    user = User.query.filter_by(username=username).first()

    if user is not None:
        code = 401
        return jsonify({'msg': 'User already exists'}), code

    new_user = User(username=username, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'msg': 'Register successfully'}), code


def verify(token: str, userid: str) -> bool:
    pass


def get_user_by_id(userid: str) -> User:
    pass

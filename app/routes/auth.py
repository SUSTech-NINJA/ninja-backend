import jwt, os
from app.models import *
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
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
            payload = {
                'username': username,
                'is_admin': False,
                'session_id': '12345'
            }
            # TODO: Update Session Database
            token = jwt.encode(payload, os.getenv('SECRET'), algorithm='HS256')

        return jsonify({'token': token}), code


def verify(token: str):
    pass

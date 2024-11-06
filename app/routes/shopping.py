from flask import Blueprint, request, jsonify
from app.models import db, User
from app.routes.auth import get_user

shopping = Blueprint('shopping', __name__)


@shopping.route('/shop/current', methods=['GET'])
def get_user_balance():
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    return jsonify({'current': user.current}), 200


@shopping.route('/shop/buy_package', methods=['POST'])
def but_package():
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    user.current = request.form['result']
    db.session.commit()
    return jsonify({'result': user.current}), 200

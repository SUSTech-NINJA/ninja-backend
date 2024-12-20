from flask import Blueprint, request, jsonify
from app.models import db, User, Bill
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
def buy_package():
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    origin_current = user.current
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    user.current = request.form['result']
    margin = int(origin_current) - round(float(user.current))
    bill = Bill(user_id=user.id, bill=margin)
    db.session.add(bill)
    db.session.commit()
    return jsonify({'result': user.current}), 200


def rewarding(uuid: str, reward):
    try:
        user = User.query.filter_by(id=uuid).first()
        user.current = user.current + reward
        db.session.commit()
        print("[INFO] Reward success: ", uuid)
    except:
        pass

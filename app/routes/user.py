from flask import Blueprint, request, jsonify
from app.routes.auth import get_user

user = Blueprint('user', __name__)

@user.route('/settings', methods=['GET', 'POST'])
def settings():
    """
    TBD
    """
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        pass


@user.route('/post', methods=['POST'])
def post():
    """
    TBD
    """
    pass


@user.route('/user/search', methods=['GET'])
def search_user():
    """
    TBD
    """
    pass


@user.route('/user/<userid>', methods=['GET'])
def get_user(userid):
    """
    TBD
    """
    pass


@user.route('/conversation/<uuid>', methods=['GET'])
def conversation(uuid):
    """
    TBD
    """
    pass


@user.route('/send_message', methods=['POST'])
def send_message():
    """
    TBD
    """
    pass


@user.route('/get_history/<uuid>', methods=['GET'])
def get_history(uuid):
    """
    TBD
    """
    pass


@user.route('/evaluate_user/<uuid>', methods=['POST'])
def evaluate_user(uuid):
    """
    TBD
    """
    pass

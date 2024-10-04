import os
import re
from flask import Blueprint, request, jsonify, Response, current_app
from openai import OpenAI
from app.routes.auth import get_user
from app.models import db, Chat
from urllib.parse import urlparse

chat = Blueprint('chat', __name__)
headers = {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'X-Accel-Buffering': 'no',
}


@chat.route('/chat/new', methods=['POST'])
def create_chat():
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    try:
        new_chat = Chat(
            user_id=user.id,
            title="New Chat",
            history=[{"role": "system", "content": request.json['prompts']}],
            settings={"model": request.json['model']}
        )
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400

    db.session.add(new_chat)
    db.session.commit()

    return jsonify({'chatid': new_chat.id}), 200


@chat.route('/chat/<chatid>', methods=['POST', 'DELETE'])
def chat_stream(chatid):
    if request.method == 'POST':
        token = request.headers.get('Authorization').split()[1]
        message = request.form.get('message')
        single_round = request.form.get('single-round').lower() == 'true'

        user = get_user(token)
        if user is None:
            return jsonify({'msg': 'Invalid Credential'}), 401

        if re.match(r'[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', chatid) is None:
            return jsonify({'msg': 'Invalid Chat ID'}), 404

        chat_info = Chat.query.filter_by(id=chatid).first()
        if chat_info is None:
            return jsonify({'msg': 'Chat not found'}), 404

        if chat_info.user_id != user.id:
            return jsonify({'msg': 'Invalid Credential'}), 401

        chat_info.history = chat_info.history + [{"role": "user", "content": message}]
        db.session.commit()

        if single_round:
            messages = [chat_info.history[0]] + [{"role": "user", "content": message}]
        else:
            messages = chat_info.history

        response = OpenAI(
            api_key=os.getenv('AIPROXY_API_KEY'),
            base_url="https://api.aiproxy.io/v1"
        ).chat.completions.create(
            messages=messages,
            model=chat_info.settings['model'],
            stream=True,
            timeout=20
        )

        def generate():
            for trunk in response:
                if trunk.choices[0].finish_reason != "stop":
                    yield trunk.choices[0].delta.content
        return Response(generate(), mimetype="text/event-stream", headers=headers)

    elif request.method == 'DELETE':
        token = request.headers.get('Authorization').split()[1]
        user = get_user(token)

        if user is None:
            return jsonify({'msg': 'Invalid Credential'}), 401

        chat_info = Chat.query.filter_by(id=chatid).first()
        if chat_info is None:
            return jsonify({'msg': 'Chat not found'}), 404

        if chat_info.user_id != user.id:
            return jsonify({'msg': 'Invalid Credential'}), 401

        db.session.delete(chat_info)
        db.session.commit()

        return jsonify({'msg': 'Chat deleted'}), 200


@chat.route('/title/<chatid>', methods=['POST'])
def title():
    pass


@chat.after_request
def after_request(response):
    path = urlparse(request.url).path
    try:
        chatid = re.search(r'/chat/([0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})', path).group(1)
        chat_info = Chat.query.filter_by(id=chatid).first()
        if chat_info is not None:
            chat_info.history = chat_info.history + [{"role": "assistant", "content": response.data.decode()}]
            db.session.commit()
    except AttributeError:
        pass
    return response

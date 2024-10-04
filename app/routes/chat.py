import os
from flask import Blueprint, request, jsonify, Response
from openai import OpenAI
from app.routes.auth import get_user
from app.models import db, Chat

chat = Blueprint('chat', __name__)


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


@chat.route('/chat/<chatid>', methods=['POST'])
def chat_stream(chatid):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    message = request.form.get('message')
    single_round = request.form.get('single-round')
    print(type(single_round))

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    chat_info = Chat.query.filter_by(id=chatid).first()

    if chat_info is None:
        return jsonify({'msg': 'Chat not found'}), 404

    if chat_info.user_id != user.id:
        return jsonify({'msg': 'Invalid Credential'}), 401

    client = OpenAI(
        api_key=os.getenv('AIPROXY_API_KEY'),
        base_url="https://api.aiproxy.io/v1"
    )

    chat_info.history = chat_info.history + [{"role": "user", "content": message}]

    response = client.chat.completions.create(
        messages=chat_info.history,
        model="gpt-3.5-turbo",
        stream=True,
        timeout=20
    )

    def generate():
        for trunk in response:
            if trunk.choices[0].finish_reason != "stop":
                yield trunk.choices[0].delta.content

    chat_info.history = chat_info.history + [{
        "role": "assistant",
        "content": ''.join([trunk.choices[0].delta.content for trunk in response if trunk.choices[0].finish_reason != "stop"])
    }]
    db.session.commit()

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
    }

    return Response(generate(), mimetype="text/event-stream", headers=headers)

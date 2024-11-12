import io
import os
import re
import json
import base64
from flask import Blueprint, request, jsonify, Response, stream_with_context
from openai import OpenAI
from app.routes.auth import get_user
from app.models import db, Chat


chat = Blueprint('chat', __name__)

headers = {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'X-Accel-Buffering': 'no',
}

# TODO: Fold Authorization to before_request
@chat.route('/chat/new', methods=['POST'])
def create_chat():
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    try:
        new_chat = Chat(
            user_id=user.id,
            title="New Conversation",
            history=[{"role": "system", "content": request.json['prompts']}],
            settings={
                "model": request.json['model']
            },
            robotid=request.json['robotid']
        )
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400

    db.session.add(new_chat)
    db.session.commit()

    return jsonify({'chatid': new_chat.id}), 200


def send_chat(chatid, use_model='', should_use_model=False):
    token = request.headers.get('Authorization').split()[1]

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

    message = request.get_json().get('message')
    files = request.get_json().get('files')
    mimetypes = request.get_json().get('mimetypes')
    single_round = request.get_json().get('single-round')

    files = json.loads(files)
    mimetypes = json.loads(mimetypes)
    assert len(files) == len(mimetypes)

    input_files = []
    for i in range(len(files)):
        if mimetypes[i].startswith('image'):
            input_files.append({
                "type": "image_url",
                "image_url": { "url": files[i] }
            })
        else:
            input_files.append({
                "type": "text",
                "text": str(base64.b64decode(files[i].replace('data:text/plain;base64,', '')))[2:-1]
            })

    if len(input_files) == 0:
        user_message = [{"role": "user", "content": message}]
    else:
        user_message = [{
            "role": "user",
            "content": [{"type": "text", "text": message}] + input_files
        }]

    chat_info.history = chat_info.history + user_message
    db.session.commit()

    response = OpenAI(
        api_key=os.getenv('AIPROXY_API_KEY'),
        base_url="https://api.aiproxy.io/v1"
    ).chat.completions.create(
        messages=(chat_info.history[:1] + user_message) if single_round else chat_info.history,
        model=chat_info.settings['model'] if should_use_model is False else use_model,
        stream=True,
        timeout=20
    )

    def generate():
        message = []
        for trunk in response:
            if trunk.choices[0].finish_reason != "stop":
                yield trunk.choices[0].delta.content
                message.append(trunk.choices[0].delta.content)
            else:
                chat_info.history = chat_info.history + [{
                    "role": "assistant",
                    "content": ''.join(message)
                }]
                db.session.commit()

    return Response(stream_with_context(generate()), mimetype="text/plain")

@chat.route('/chat/<chatid>/use/<model>',methods=['POST'])
def chat_use_model(chatid, model):
    return send_chat(chatid, model, True)

@chat.route('/chat/<chatid>', methods=['GET', 'POST', 'DELETE'])
def chat_stream(chatid):
    """
    TBD
    """
    if request.method == 'GET':
        token = request.headers.get('Authorization').split()[1]
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

        return jsonify({
            'base-model': chat_info.settings['model'],
            'title': chat_info.title,
            'messages': chat_info.history,
            'robotid': chat_info.robotid
        }), 200

    # Get Response From GPT
    elif request.method == 'POST':
        return send_chat(chatid)

    # Delete Chat
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


@chat.route('/title/<chatid>', methods=['GET'])
def title(chatid):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    chat_info = Chat.query.filter_by(id=chatid).first()
    if chat_info is None:
        return jsonify({'msg': 'Chat not found'}), 404

    if chat_info.user_id != user.id:
        return jsonify({'msg': 'Invalid Credential'}), 401

    with open('app/assets/prompts.json', 'r') as f:
        prompt = json.load(f)[0][1]

    history = []
    for message in chat_info.history[1:]:
        if isinstance(message['content'], str):
            history.append(message)
        else:
            history.append({
                'role': message['role'],
                'content': message['content'][0]['text']
            })
    message = [{"role": "system", "content": prompt}] + history

    response = OpenAI(
        api_key=os.getenv('AIPROXY_API_KEY'),
        base_url="https://api.aiproxy.io/v1"
    ).chat.completions.create(
        messages=message,
        model='gpt-3.5-turbo',
        stream=True,
        timeout=20
    )

    def generate():
        message = []
        for trunk in response:
            if trunk.choices[0].finish_reason != "stop":
                yield trunk.choices[0].delta.content
                message.append(trunk.choices[0].delta.content)
            else:
                chat_info.title = ''.join(message)
                db.session.commit()

    return Response(stream_with_context(generate()), mimetype="text/plain")


@chat.route('/chat', methods=['GET'])
def get_chats():
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    chats = Chat.query.filter_by(user_id=user.id).all()
    return jsonify([{'chatid': chat.id, 'title': chat.title} for chat in chats]), 200


@chat.route('/chat/clear/<chatid>', methods=['POST'])
def clear_chat(chatid):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    chat_info = Chat.query.filter_by(id=chatid).first()

    if chat_info is None:
        return jsonify({'msg': 'Chat not found'}), 404

    if chat_info.user_id != user.id:
        return jsonify({'msg': 'Invalid Credential'}), 401

    chat_info.history = chat_info.history[:1]
    db.session.commit()

    return jsonify({'msg': 'Success'}), 200


@chat.route('/chat/edit/<chatid>', methods=['POST'])
def edit_chat(chatid):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    chat_info = Chat.query.filter_by(id=chatid).first()

    if chat_info is None:
        return jsonify({'msg': 'Chat not found'}), 404

    if chat_info.user_id != user.id:
        return jsonify({'msg': 'Invalid Credential'}), 401

    chat_info.title = request.form.get('title')
    db.session.commit()

    return jsonify({'msg': 'Success'}), 200


@chat.route('/chat/optimize', methods=['POST'])
def optimize():
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    with open('app/assets/prompts.json', 'r') as f:
        message = [
            {"role": "system", "content": json.load(f)[1][1]},
            {"role": "user", "content": request.form.get('text')}
        ]

    print(message)

    response = OpenAI(
        api_key=os.getenv('AIPROXY_API_KEY'),
        base_url="https://api.aiproxy.io/v1"
    ).chat.completions.create(
        messages=message,
        model='gpt-3.5-turbo',
        timeout=20
    )

    return response.choices[0].message.content, 200


@chat.route('/chat/suggestions/<chatid>', methods=['GET'])
def suggest(chatid):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    chat_info = Chat.query.filter_by(id=chatid).first()
    if chat_info is None:
        return jsonify({'msg': 'Chat not found'}), 404

    if chat_info.user_id != user.id:
        return jsonify({'msg': 'Invalid Credential'}), 401

    with open('app/assets/prompts.json', 'r') as f:
        prompt = json.load(f)[2][1]

    history = []
    for message in chat_info.history[1:]:
        if isinstance(message['content'], str):
            history.append(message)
        else:
            history.append({
                'role': message['role'],
                'content': message['content'][0]['text']
            })
    message = [{"role": "system", "content": prompt}] + history

    response = OpenAI(
        api_key=os.getenv('AIPROXY_API_KEY'),
        base_url="https://api.aiproxy.io/v1"
    ).chat.completions.create(
        messages=message,
        model='gpt-3.5-turbo',
        timeout=20
    )

    return response.choices[0].message.content, 200

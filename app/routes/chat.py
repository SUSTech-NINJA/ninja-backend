import os
import re
import json
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
            }
        )
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400

    db.session.add(new_chat)
    db.session.commit()

    return jsonify({'chatid': new_chat.id}), 200


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
            'messages': chat_info.history
        }), 200

    # Get Response From GPT
    elif request.method == 'POST':
        # TODO: Add file upload support
        token = request.headers.get('Authorization').split()[1]
        message = request.get_json().get('message')
        single_round = request.get_json().get('single-round')

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

        # TODO: Get bot information from database, i.e., url
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
            message = []
            for trunk in response:
                if trunk.choices[0].finish_reason != "stop":
                    yield trunk.choices[0].delta.content
                    message.append(trunk.choices[0].delta.content)
                else:
                    chat_info.history = chat_info.history + [{"role": "assistant", "content": ''.join(message)}]
                    db.session.commit()

        return Response(stream_with_context(generate()), mimetype="text/plain")

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
    message = [{"role": "system", "content": prompt}] + chat_info.history[1:]

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

    return jsonify({"string": response.choices[0].message.content}), 200


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
    message = [{"role": "system", "content": prompt}] + chat_info.history[1:]

    response = OpenAI(
        api_key=os.getenv('AIPROXY_API_KEY'),
        base_url="https://api.aiproxy.io/v1"
    ).chat.completions.create(
        messages=message,
        model='gpt-3.5-turbo',
        timeout=20
    )

    return jsonify({"string": response.choices[0].message.content}), 200


@chat.route('/test', methods=['GET'])
def test():
    """
    TBD
    """
    # base64_image = encode_image('app/assets/1.jpeg')

    message = [
        {"role": "system", "content": "Tell me what you see"},
        {"role": "user", "content": [
            {"type":"text", "text":"What's in this image?"},
            {
               "type":"image_url",
               "image_url":{
                  "url":f"data:image/jpeg;base64,{base64_image}"
               }
            }
        ]}
    ]

    response = OpenAI(
        api_key=os.getenv('AIPROXY_API_KEY'),
        base_url="https://api.aiproxy.io/v1"
    ).chat.completions.create(
        messages=message,
        model='gpt-4-turbo',
        timeout=20
    )

    return jsonify({"string": response.choices[0].message.content}), 200

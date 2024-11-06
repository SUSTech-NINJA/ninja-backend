# Generating Response in Stream

下面是GPT流式回复的示例代码：

```python
@chat.route('/stream', methods=['POST'])
def test():
    response = OpenAI(
        api_key=os.getenv('AIPROXY_API_KEY'),
        base_url="https://api.aiproxy.io/v1"
    ).chat.completions.create(
        messages=[{"role": "system", "content": "Hello, how are you?"}],
        model='gpt-3.5-turbo',
        stream=True,
        timeout=20
    )

    def stream():
        for trunk in response:
            if trunk.choices[0].finish_reason != "stop":
                yield trunk.choices[0].delta.content
                time.sleep(0.3)
    return Response(stream(), mimetype='text/plain', headers=headers)
```

from flask import Flask, Response, request
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)  # 允许跨域，前端才能调用

client = OpenAI(
    api_key="sk-0ee20bfef91c4c17bcb815a69e9a5a99",
    base_url="https://api.deepseek.com"
)
chat_history = []
MAX_ROUNDS = 5
system_prompt = (
        "生成完整HTML5小游戏,具备基本功能,尺寸正确的游戏,代码简洁紧凑,只能生成html代码,直接输出代码,记住上一次游戏内容,支持修改、优化、微调游戏，不要多余解释文字。"
    )

@app.route("/api/generate-game", methods=["POST"])
def generate_game():
    data = request.get_json()
    prompt = data.get("prompt", "射击游戏")
    chat_history.append({"role":"user","content":prompt})

    def stream():
        messages = [{"role":"system","content":system_prompt}]
        messages.extend(chat_history)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.2,
            stream=False
        )
        content = response.choices[0].message.content
        chat_history.append({"role":"assistant","content":content})

        while len(chat_history) > MAX_ROUNDS * 2:
            chat_history.pop(0)
            chat_history.pop(0)

        yield content

    return Response(stream(), content_type="text/html; charset=utf-8")
# 清空记忆
@app.route("/api/clear",methods=["POST"])
def clear():
    chat_history.clear()
    return {"ok":True}
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
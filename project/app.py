import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
from openai import OpenAI
import requests

app = Flask(__name__)
CORS(app)

# API 金鑰
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GROK_API_KEY = os.getenv('GROK_API_KEY')

# 初始化 Gemini 和 OpenAI 客戶端
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/ai', methods=['POST'])
def ai_response():
    data = request.json
    prompt = data.get('prompt', '')
    role = data.get('role', '一般人')
    model = data.get('model', 'gemini')

    if not prompt:
        return jsonify({'reply': '請提供問題！'}), 400

    # 角色提示詞
    role_prompts = {
    "國小生": f"你是一位親切的小學老師，正在向小學生解釋這個問題。請用簡單、溫柔的語氣講幾句話，控制在 100 字以內。可以加入一點小故事或比喻幫助理解。難的字旁邊加上注音（像這樣：制度(ㄓˋ ㄉㄨˋ)）。請回答這個問題：{prompt}",
    "國中生": f"你是國中老師，正在幫學生釐清這個問題。請用清楚、有條理的方式回答，內容控制在 150 字以內，並舉一個簡單的例子幫助理解：{prompt}",
    "高中生": f"你是高中老師，要引導學生理解這個問題。請用邏輯清楚的方式回答，內容控制在 200 字以內，可以加入簡單分析或觀點：{prompt}",
    "一般人": f"請用一般大眾都能理解的方式來說明這個問題，回答請控制在 200 字以內，重點清楚、不要太學術：{prompt}"
}

    final_prompt = role_prompts.get(role, prompt)

    try:
        if model == 'gemini':
            response = gemini_model.generate_content(final_prompt)
            reply = response.text

        elif model == 'chatgpt':
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個有幫助的AI助理"},
                    {"role": "user", "content": final_prompt}
                ]
            )
            reply = response.choices[0].message.content

        elif model == 'grok':
            headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "grok-2",  # 根據官方更新模型名
                "messages": [{"role": "user", "content": final_prompt}],
                "temperature": 0.7
            }
            grok_response = requests.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers)
            grok_response.raise_for_status()
            reply = grok_response.json()["choices"][0]["message"]["content"]

        else:
            reply = "❌ 未知的 AI 模型"

        return jsonify({'reply': reply})

    except requests.exceptions.RequestException as e:
        return jsonify({'reply': f'API 請求錯誤：{str(e)}'}), 500
    except Exception as e:
        return jsonify({'reply': f'伺服器錯誤：{str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)



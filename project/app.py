import os
from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import google.generativeai as genai
from openai import OpenAI
import requests
import sqlite3

app = Flask(__name__)
CORS(app)

# SQLite 絕對路徑
DB_FOLDER = os.path.join(os.path.dirname(__file__), "sql")
os.makedirs(DB_FOLDER, exist_ok=True)
DB_PATH = os.path.join(DB_FOLDER, "chat.db")

# 初始化資料庫
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school TEXT,
            studentID TEXT,
            studentName TEXT,
            question TEXT,
            gemini_answer TEXT,
            chatgpt_answer TEXT,
            grok_answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# API 金鑰
GEMINI_API_KEY = 'AIzaSyDMzb6ItrsJUrbjTeBplM1s2eAZWAN-UoA'
OPENAI_API_KEY = 'sk-proj-ldR6HTSNODR0vPkgkb-...'  # 示意
GROK_API_KEY = 'xai-u2o9NsbLrfdq5bC1NjLXmG3nZvfkUPuU2RNfJqHvcNWW0stnrw0I8Na8yPTsYY8SIzuQurLXrj99TixM'

# 初始化 Gemini 和 OpenAI 客戶端
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# HTML 路由
# -----------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/student')
def student_page():
    return render_template('index.html')

@app.route('/teacher')
def teacher_page():
    return render_template('teacher.html')

@app.route("/form")
def go_form():
    return redirect("https://docs.google.com/forms/d/e/1FAIpQLScK47610c42TO-XS2Xatzn7R7PtatvPuX_2_oaQYr4ZoLcWZQ/viewform")

# -----------------------------
# AI API
# -----------------------------
@app.route('/api/ai', methods=['POST'])
def ai_response():
    data = request.json
    prompt = data.get('prompt', '')
    role = data.get('role', '一般人')
    model = data.get('model', 'gemini')

    if not prompt:
        return jsonify({'reply': '請提供問題！'}), 400

    role_prompts = {
        "國小生": f"你是一位親切的小學老師，請回答這個問題：{prompt}",
        "國中生": f"你是國中老師，請回答這個問題：{prompt}",
        "高中生": f"你是高中老師，請回答這個問題：{prompt}",
        "一般人": f"請用大眾能理解方式回答：{prompt}"
    }

    final_prompt = role_prompts.get(role, prompt)

    try:
        if model == 'gemini':
            response = gemini_model.generate_content(final_prompt)
            reply = response.text
        elif model == 'chatgpt':
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "你是一個有幫助的AI助理"},
                          {"role": "user", "content": final_prompt}]
            )
            reply = response.choices[0].message.content
        elif model == 'grok':
            headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "grok-2", "messages":[{"role": "user", "content": final_prompt}], "temperature":0.7}
            grok_response = requests.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers)
            grok_response.raise_for_status()
            reply = grok_response.json()["choices"][0]["message"]["content"]
        else:
            reply = "❌ 未知的 AI 模型"

        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'reply': f'伺服器錯誤：{str(e)}'}), 500

# -----------------------------
# 學生紀錄
# -----------------------------
@app.post("/save_record")
def save_record():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO records (school, studentID, studentName, question, gemini_answer, chatgpt_answer, grok_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data["school"],
        data["studentID"],
        data["studentName"],
        data["question"],
        data["responses"]["gemini"],
        data["responses"]["chatgpt"],
        data["responses"]["grok"]
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

@app.get("/get_records")
def get_records():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM records ORDER BY id DESC")
    rows = c.fetchall()
    records = [dict(row) for row in rows]
    conn.close()
    return jsonify(records)

# -----------------------------
# 啟動程式（本地開發版本）
# -----------------------------
init_db()
if __name__ == '__main__':
    app.run(debug=True)  # 本地開發用






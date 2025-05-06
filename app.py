from flask import Flask, request, render_template, jsonify
import sqlite3
import os
from datetime import datetime
import pytz

app = Flask(__name__)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "blog.db")

# 时区设置为香港/中国大陆 (UTC+8)
HONGKONG_TZ = pytz.timezone("Asia/Hong_Kong")

# 初始化数据库
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# 转换时间为香港时区
def convert_to_hongkong_time(timestamp):
    # 将字符串时间转换为 datetime 对象
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    dt = pytz.utc.localize(dt).astimezone(HONGKONG_TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 保存笔记
@app.route("/api/save", methods=["POST"])
def save_note():
    try:
        data = request.json
        title = data.get("title")
        content = data.get("content")
        if not title or not content:
            return jsonify({"error": "Title and content are required"}), 400
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取所有笔记（仅标题）
@app.route("/api/notes", methods=["GET"])
def get_notes():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, created_at FROM notes ORDER BY created_at DESC")
            notes = [{"id": row[0], "title": row[1], "created_at": convert_to_hongkong_time(row[2])} for row in cursor.fetchall()]
        return jsonify(notes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取单篇笔记（详细内容）
@app.route("/api/note/<int:note_id>", methods=["GET"])
def get_note(note_id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, content, created_at FROM notes WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            if row:
                return jsonify({"title": row[0], "content": row[1], "created_at": convert_to_hongkong_time(row[2])})
            return jsonify({"error": "Note not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 主页（标题列表）
@app.route("/")
def index():
    return render_template("index.html")

# 详细内容页
@app.route("/note/<int:note_id>")
def note_detail(note_id):
    return render_template("note.html", note_id=note_id)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5001)
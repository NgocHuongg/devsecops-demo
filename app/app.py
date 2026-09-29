"""
App Flask demo — BẢN ĐÃ VÁ các lỗi mức ERROR (SAST gate PASS).
Cố ý GIỮ LẠI lỗi mức WARNING (MD5, Flask debug) để chứng minh
security gate chỉ chặn ERROR, WARNING chỉ cảnh báo.
"""
import ast
import hashlib
import json
import sqlite3
import subprocess

from flask import Flask, request

app = Flask(__name__)

# LỖ HỔNG 1: Hardcoded credential (CWE-798)
DB_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"


def get_db():
    return sqlite3.connect("users.db")


@app.route("/user")
def find_user():
    name = request.args.get("name", "")
    db = get_db()
    # ĐÃ VÁ: parameterized query thay vì nối chuỗi (CWE-89)
    rows = db.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall()
    return str(rows)


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    # ĐÃ VÁ: subprocess với list args, không qua shell (CWE-78)
    output = subprocess.run(
        ["ping", "-c", "1", host], capture_output=True, text=True
    ).stdout
    return output


@app.route("/calc")
def calc():
    expr = request.args.get("expr", "1+1")
    # ĐÃ VÁ: ast.literal_eval chỉ tính biểu thức an toàn (CWE-95)
    return str(ast.literal_eval(expr))


@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password", "")
    # LỖ HỔNG 5: Hash yếu MD5 cho mật khẩu (CWE-916)
    hashed = hashlib.md5(password.encode()).hexdigest()
    return hashed


@app.route("/profile", methods=["POST"])
def load_profile():
    data = request.get_data()
    # ĐÃ VÁ: json.loads thay vì pickle.loads (CWE-502)
    profile = json.loads(data)
    return str(profile)


@app.route("/debug")
def debug_info():
    # LỖ HỔNG 7: Flask debug mode (CWE-489)
    app.run(debug=True)
    return "debug"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

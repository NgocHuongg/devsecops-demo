"""
App Flask mẫu CÓ CHỦ ĐÍCH DÍNH LỖ HỔNG BẢO MẬT
Mục đích: làm mục tiêu cho SAST (Semgrep) — KHÔNG dùng trong sản xuất thật.
"""
import hashlib
import os
import pickle
import sqlite3

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
    # LỖ HỔNG 2: SQL Injection (CWE-89) — nối chuỗi trực tiếp vào truy vấn
    query = "SELECT * FROM users WHERE name = '" + name + "'"
    rows = db.execute(query).fetchall()
    return str(rows)


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    # LỖ HỔNG 3: Command Injection (CWE-78) — user input vào shell
    output = os.popen("ping -c 1 " + host).read()
    return output


@app.route("/calc")
def calc():
    expr = request.args.get("expr", "1+1")
    # LỖ HỔNG 4: Eval injection (CWE-95) — thực thi mã tùy ý
    return str(eval(expr))


@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password", "")
    # LỖ HỔNG 5: Hash yếu MD5 cho mật khẩu (CWE-916)
    hashed = hashlib.md5(password.encode()).hexdigest()
    return hashed


@app.route("/profile", methods=["POST"])
def load_profile():
    data = request.get_data()
    # LỖ HỔNG 6: Insecure deserialization (CWE-502) — pickle với dữ liệu người dùng
    profile = pickle.loads(data)
    return str(profile)


@app.route("/debug")
def debug_info():
    # LỖ HỔNG 7: Flask debug mode (CWE-489)
    app.run(debug=True)
    return "debug"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

@app.route("/run")
def run_cmd():
    import os
    return os.popen("ls " + request.args.get("dir")).read()

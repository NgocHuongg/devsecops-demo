"""Bản ĐÃ VÁ các lỗ hổng — dùng để chứng minh security gate cho PASS khi code sạch."""
import hashlib
import sqlite3

from flask import Flask, request

app = Flask(__name__)


def get_db():
    return sqlite3.connect("users.db")


@app.route("/user")
def find_user():
    name = request.args.get("name", "")
    db = get_db()
    # ĐÃ VÁ: dùng parameterized query thay vì nối chuỗi
    rows = db.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall()
    return str(rows)


@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password", "")
    # ĐÃ VÁ: dùng SHA-256 thay vì MD5
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

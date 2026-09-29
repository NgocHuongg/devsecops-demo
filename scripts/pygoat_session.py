"""
Tạo sẵn 1 phiên đăng nhập Django cho ZAP (authenticated DAST) — không cần mật khẩu.
Chạy BÊN TRONG container PyGoat:
    docker exec -i pygoat python3 pygoat/manage.py shell < scripts/pygoat_session.py
In ra ở dòng cuối giá trị header Cookie (sessionid + csrftoken cố định) để ZAP gắn vào mọi request.
"""
from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY, get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.utils.crypto import get_random_string

User = get_user_model()
user, _ = User.objects.get_or_create(username="zap-scanner")
user.set_unusable_password()  # tài khoản chỉ dùng cho máy quét, không đăng nhập bằng mật khẩu được
user.save()

session = SessionStore()
session[SESSION_KEY] = str(user.pk)
session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
session[HASH_SESSION_KEY] = user.get_session_auth_hash()
session.create()
# csrftoken cố định: Django sinh csrfmiddlewaretoken trong form từ cookie này,
# nên ZAP gửi lại form POST vẫn qua được kiểm tra CSRF
csrf = get_random_string(32)
print(f"sessionid={session.session_key}; csrftoken={csrf}")

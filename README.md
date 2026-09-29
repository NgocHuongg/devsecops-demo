# DevSecOps Demo — SAST & DAST cho ứng dụng Web

Demo quy trình DevSecOps tích hợp kiểm thử bảo mật tự động.

## Cấu trúc

```
├── app/                  # Flask app CÓ CHỦ ĐÍCH dính lỗ hổng (mục tiêu cho SAST)
├── app-fixed/            # Bản đã vá — chứng minh gate PASS khi code sạch
├── docker-compose.yml    # Juice Shop (mục tiêu DAST) + OWASP ZAP (máy quét)
├── scan-sast.sh          # Chạy SAST local bằng Docker
└── .github/workflows/security.yml   # Pipeline CI: SAST + security gate
```

## Cách dùng

```bash
# Môi trường DAST (Juice Shop + ZAP)
docker compose up -d
# Juice Shop: http://localhost:3000 — ZAP API: http://localhost:8080

# SAST local
./scan-sast.sh
```

## Security gate

Pipeline FAIL khi Semgrep phát hiện lỗi mức ERROR (SQL injection, command injection,
eval injection, insecure deserialization...). Lỗi WARNING chỉ cảnh báo, không chặn.

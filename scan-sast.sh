#!/usr/bin/env bash
# Chạy SAST local bằng Docker — giống hệt bước trong CI
# Cách dùng: ./scan-sast.sh
set -e
# Git Bash trên Windows tự đổi "/src/..." thành "C:/Program Files/Git/src/..." → tắt đi
export MSYS_NO_PATHCONV=1

# pwd -W cho đường dẫn Windows (C:/...) để Docker mount được
APP_DIR="$(pwd -W 2>/dev/null || pwd)/app"

echo "==> Quét SAST với Semgrep trên: $APP_DIR"
docker run --rm -v "$APP_DIR:/src" semgrep/semgrep semgrep \
  --config p/owasp-top-ten \
  --config p/security-audit \
  --metrics=off \
  --sarif --output /src/semgrep.sarif \
  /src

echo "==> Báo cáo SARIF: $APP_DIR/semgrep.sarif"

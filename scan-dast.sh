#!/usr/bin/env bash
# Quét DAST local bằng Docker — giống hệt job DAST trong CI.
# Yêu cầu: Juice Shop đang chạy (docker compose up -d).
# Cách dùng: ./scan-dast.sh
set -e

REPORTS="$(pwd -W 2>/dev/null || pwd)/reports"
mkdir -p "$REPORTS"
chmod 777 "$REPORTS" 2>/dev/null || true

echo "==> Tao network scan-net + chay Juice Shop muc tieu"
docker network create scan-net >/dev/null 2>&1 || true
docker rm -f zap-target >/dev/null 2>&1 || true
docker run -d --name zap-target -p 3100:3000 --network scan-net bkimminich/juice-shop >/dev/null

echo "==> Cho app san sang..."
for i in $(seq 1 30); do
  curl -sf http://localhost:3100 >/dev/null 2>&1 && break
  sleep 2
done

echo "==> ZAP baseline scan (passive)"
docker run --rm --network scan-net \
  -v "$REPORTS:/zap/wrk:rw" zaproxy/zap-stable \
  zap-baseline.py -t http://zap-target:3000 \
  -J zap-dast.json -r zap-dast.html -m 5 -I

echo "==> DAST gate"
python3 scripts/check_dast.py "$REPORTS/zap-dast.json"

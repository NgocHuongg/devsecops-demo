#!/usr/bin/env bash
# Quét SAST + DAST trên CÙNG ứng dụng PyGoat — giống workflow
# .github/workflows/pygoat-scan.yml. Gate FAIL vẫn chạy tiếp để ra đủ báo cáo.
# Cách dùng: ./scan-pygoat.sh
set -e
# Git Bash trên Windows tự đổi "/work/..." thành "C:/Program Files/Git/work/..." → tắt đi
export MSYS_NO_PATHCONV=1

IMAGE="pygoat/pygoat@sha256:26a75f7cd023a9c77158f55c54dbb405ab2b77aaf46dfb888f209735fa0d0b54"
REPORTS="$(pwd -W 2>/dev/null || pwd)/reports"
mkdir -p reports
chmod 777 reports 2>/dev/null || true

echo "==> [SAST] Lay ma nguon tu image + quet Semgrep"
rm -rf reports/pygoat-src
docker rm -f pygoat-src >/dev/null 2>&1 || true
docker create --name pygoat-src "$IMAGE" >/dev/null
docker cp pygoat-src:/app/pygoat reports/pygoat-src
docker rm pygoat-src >/dev/null
docker run --rm -v "$REPORTS:/work" semgrep/semgrep semgrep \
  --config p/owasp-top-ten \
  --config p/security-audit \
  --config p/django \
  --metrics=off \
  --json-output /work/pygoat-semgrep.json \
  /work/pygoat-src
python3 scripts/check_sast.py reports/pygoat-semgrep.json || true

echo "==> [DAST] Chay PyGoat muc tieu"
docker network create pygoat-net >/dev/null 2>&1 || true
docker rm -f pygoat-target >/dev/null 2>&1 || true
docker run -d --name pygoat-target -p 8100:8000 --network pygoat-net \
  --network-alias pygoat "$IMAGE" >/dev/null
for i in $(seq 1 30); do
  curl -sf http://localhost:8100/login/ >/dev/null 2>&1 && break
  sleep 2
done

echo "==> [DAST] Tao phien dang nhap cho ZAP"
COOKIE=$(docker exec -i pygoat-target python3 pygoat/manage.py shell < scripts/pygoat_session.py | tail -1)

echo "==> [DAST] ZAP full scan (spider + passive + active)"
docker run --rm --network pygoat-net \
  -v "$REPORTS:/zap/wrk:rw" zaproxy/zap-stable \
  zap-full-scan.py -t http://pygoat:8000/ \
  -J pygoat-zap.json -r pygoat-zap.html -m 3 -I \
  -z "-config replacer.full_list(0).description=auth \
      -config replacer.full_list(0).enabled=true \
      -config replacer.full_list(0).matchtype=REQ_HEADER \
      -config replacer.full_list(0).matchstr=Cookie \
      -config replacer.full_list(0).regex=false \
      -config 'replacer.full_list(0).replacement=$COOKIE' \
      -config globalexcludeurl.url_list.url(0).regex=.*logout.* \
      -config globalexcludeurl.url_list.url(0).description=logout \
      -config globalexcludeurl.url_list.url(0).enabled=true \
      -config scanner.maxScanDurationInMins=20"
python3 scripts/check_dast.py reports/pygoat-zap.json || true

echo "==> Bao cao: reports/pygoat-semgrep.json, reports/pygoat-zap.html"

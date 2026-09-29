"""
SAST gate: FAIL nếu Semgrep có finding mức ERROR.
Cách dùng: python check_sast.py <báo_cáo_semgrep.json>
Đọc JSON của Semgrep (--json / --json-output). Chỉ cần quét 1 lần, không phải
chạy lại Semgrep với --severity ERROR như job SAST cũ.
"""
import json
import os
import sys


def load_results(path):
    if not os.path.exists(path):
        print(f"::error::Khong tim thay bao cao SAST: {path}")
        sys.exit(2)
    if os.path.getsize(path) == 0:
        print(f"::error::Bao cao SAST trong rong: {path}")
        sys.exit(2)
    return json.load(open(path, encoding="utf-8"))["results"]


def main():
    results = load_results(sys.argv[1])
    counts = {}
    errors = []
    for r in results:
        sev = r["extra"]["severity"]
        counts[sev] = counts.get(sev, 0) + 1
        if sev == "ERROR":
            errors.append(r)

    print(f"== SAST ket qua: {len(results)} finding ==")
    for sev in ("ERROR", "WARNING", "INFO"):
        if sev in counts:
            print(f"   {sev}: {counts[sev]}")
    for r in errors:
        rule = r["check_id"].split(".")[-1]
        print(f"   [ERROR] {r['path']}:{r['start']['line']} {rule}")

    if errors:
        print(f"::error::SAST gate FAIL: {len(errors)} finding muc ERROR")
        sys.exit(1)
    print("==> GATE PASS: khong co finding ERROR")
    sys.exit(0)


if __name__ == "__main__":
    main()

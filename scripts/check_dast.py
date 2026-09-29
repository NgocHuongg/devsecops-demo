"""
DAST gate: FAIL nếu ZAP phát hiện cảnh báo mức High.
Cách dùng: python check_dast.py <báo_cáo_zap.json>
Đọc được cả 2 định dạng: JSON của zap-baseline.py (-J) và của ZAP API.
"""
import json
import os
import sys

RISK = {"3": "High", "2": "Medium", "1": "Low", "0": "Informational"}


def load_alerts(path):
    if not os.path.exists(path):
        print(f"::error::Khong tim thay bao cao DAST: {path}")
        sys.exit(2)
    if os.path.getsize(path) == 0:
        print(f"::error::Bao cao DAST trong rong: {path}")
        sys.exit(2)
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict) and "alerts" in data:
        return data["alerts"]
    # zap-baseline.py JSON: {"site": [{"alerts": [...]}]}
    alerts = []
    for site in data.get("site", []):
        alerts.extend(site.get("alerts", []))
    return alerts


def main():
    alerts = load_alerts(sys.argv[1])
    counts = {}
    highs = []
    for a in alerts:
        code = str(a.get("riskcode", a.get("risk", "")))
        name = RISK.get(code, code or "Unknown")
        counts[name] = counts.get(name, 0) + 1
        if name == "High":
            highs.append(a)

    print(f"== DAST ket qua: {len(alerts)} canh bao ==")
    for name in ("High", "Medium", "Low", "Informational", "Unknown"):
        if name in counts:
            print(f"   {name}: {counts[name]}")
    for a in highs:
        print(f"   [HIGH] {a.get('alert', a.get('name', '?'))}")

    if highs:
        names = ", ".join(a.get("alert", a.get("name", "?")) for a in highs[:5])
        print(f"::error::DAST gate FAIL: {len(highs)} canh bao High - {names}")
        sys.exit(1)
    print("==> GATE PASS: khong co canh bao High")
    sys.exit(0)


if __name__ == "__main__":
    main()

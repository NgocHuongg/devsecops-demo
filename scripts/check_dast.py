"""
DAST gate: FAIL nếu ZAP phát hiện cảnh báo mức High.
Cách dùng: python check_dast.py <báo_cáo_zap.json>
Đọc được cả 2 định dạng: JSON của zap-baseline.py (-J) và của ZAP API.
"""
import json
import sys

RISK = {"3": "High", "2": "Medium", "1": "Low", "0": "Informational"}


def load_alerts(path):
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
    for a in alerts:
        code = str(a.get("riskcode", a.get("risk", "")))
        name = RISK.get(code, code or "Unknown")
        counts[name] = counts.get(name, 0) + 1

    print(f"== DAST ket qua: {len(alerts)} canh bao ==")
    for name in ("High", "Medium", "Low", "Informational", "Unknown"):
        if name in counts:
            print(f"   {name}: {counts[name]}")

    if counts.get("High", 0) > 0:
        print(f"==> GATE FAIL: phat hien {counts['High']} canh bao High")
        sys.exit(1)
    print("==> GATE PASS: khong co canh bao High")
    sys.exit(0)


if __name__ == "__main__":
    main()

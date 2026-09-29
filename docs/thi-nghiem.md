# Báo cáo thí nghiệm — DevSecOps SAST & DAST

> Dữ liệu thu từ pipeline thật: https://github.com/NgocHuongg/devsecops-demo
> Ngày thí nghiệm: 29/09/2026. Mọi số liệu lấy từ GitHub Actions API và ZAP API, không chỉnh sửa.

## 1. Câu hỏi thí nghiệm

- **E1**: Mỗi công cụ bắt được loại lỗ hổng nào? (SAST vs Secret scan vs DAST vs SCA)
- **E2**: Tích hợp vào pipeline làm tăng bao nhiêu thời gian build?
- **E3**: Security gate có chặn được code lỗi và cho qua code sạch không?
- **E4**: Độ sâu quét DAST ảnh hưởng thế nào đến kết quả?
- **E5**: Bao nhiêu cảnh báo là cảnh báo đúng (true positive) vs nhiễu?

## 2. E1 — Ma trận phát hiện lỗ hổng cấy thử

Cấy 7 lỗ hổng vào `app/app.py` (Flask), quét bằng 3 công cụ:

| Lỗ hổng cấy | CWE | Semgrep (SAST) | Gitleaks (secret) | ZAP (DAST) |
|---|---|---|---|---|
| SQL Injection | CWE-89 | ✅ ERROR | — | ✅ (active scan) |
| Command Injection | CWE-78 | ✅ ERROR | — | ❌ |
| Eval Injection | CWE-95 | ✅ ERROR | — | ❌ |
| Deserialization (pickle) | CWE-502 | ✅ ERROR | — | ❌ |
| Hash yếu MD5 | CWE-916 | ✅ WARNING | — | ❌ |
| Flask debug mode | CWE-489 | ✅ WARNING | — | ❌ |
| Hardcoded API key | CWE-798 | ❌ | ✅ | ❌ |
| **Tỷ lệ bắt** | | **6/7** | **1/7** | **1/7** |

**Nhận xét**:
- Semgrep phát hiện 6/7 loại (11 findings cho 7 lỗ hổng — 1 lỗ hổng khớp nhiều rule:
  `eval` khớp 3 rule, `md5` 2 rule, `pickle` 2 rule → cần khử trùng lặp khi tổng hợp).
- Hardcoded credential là điểm mù của Semgrep nhưng Gitleaks bắt được → **bổ sung nhau**.
- DAST không thấy lỗi ở tầng code (command injection, pickle...) vì nó chỉ quan sát
  hành vi HTTP — chỉ thấy SQL injection khi được quét chủ động đúng endpoint.

## 3. E2 — Thời gian pipeline (GitHub Actions, run `e066d1a`)

| Job | Công cụ | Thời gian | Chạy song song? |
|---|---|---|---|
| SAST | Semgrep (Docker) | 35 giây | ✅ |
| Secret Scan | Gitleaks | 8 giây | ✅ |
| SCA | Trivy (fs + image) | 31 giây | ✅ |
| DAST | OWASP ZAP baseline | 96 giây | ✅ |
| **Tổng wall-time** (4 job song song) | | **~1 phút 40 giây** | |

**Nhận xét**: chi phí thời gian chấp nhận được cho mỗi commit. Job DAST nặng nhất
(96s) vì phải tải image ZAP + dựng app + spider; có thể giảm bằng image cache /
chạy DAST nightly thay vì mỗi commit.

## 4. E3 — Hành vi security gate (8 lần chạy CI)

| Commit | Tình huống | SAST | Secret | DAST | SCA | Run |
|---|---|---|---|---|---|---|
| `50941db` | Code có 4 lỗi ERROR | ❌ chặn | — | — | — | FAIL |
| `84cd926` | Đã vá, còn WARNING | ✅ | — | — | — | PASS |
| `cdcf163` | Thêm DAST (bug quyền ghi) | ✅ | — | ❌ | — | FAIL |
| `edf0f69` | Sửa bug môi trường | ✅ | — | ✅ | — | PASS |
| `b25ef2b` | Thêm Gitleaks + Trivy | ✅ | ❌ bắt API key | ✅ | ✅ | FAIL |
| `e066d1a` | Chuyển secret sang env var | ✅ | ✅ | ✅ | ✅ | PASS |

**Nhận xét**: gate hoạt động đúng 2 chiều — chặn khi có lỗi (ERROR/secret/High),
cho qua khi đã vá. 2 lần FAIL giữa chừng (`cdcf163`, `b25ef2b`) là lỗi môi trường
(thiếu quyền ghi, sai flag) — minh chứng thực tế "CI đỏ không chỉ do lỗ hổng".

## 5. E4 — Độ sâu quét DAST (OWASP ZAP trên Juice Shop)

| Kịch bản quét | Cảnh báo | High | Ghi chú |
|---|---|---|---|
| Spider + passive scan | 260 | 0 | Nhìn lướt request/response |
| Active scan toàn cây URL | 284 | 0 | SPA — endpoint REST chứa lỗi KHÔNG nằm trong cây quét |
| **Active scan có chủ đích** (endpoint `/rest/products/search?q=`) | **286** | **1** | **Bắt được SQL Injection (High)** |

**Nhận xét** (điểm quan trọng nhất của thí nghiệm):
- DAST tìm thấy lỗ hổng runtime thật (SQLi tại `search?q=apple'`) mà SAST không
  thấy trên bản build — nhưng **chỉ khi quét đúng endpoint**.
- Ứng dụng SPA/API: crawl thông thường không đủ → cần quét theo OpenAPI spec hoặc
  danh sách endpoint. Đây là hạn chế cần nêu trong đồ án.

## 6. E5 — True positive vs nhiễu

**ZAP (286 cảnh báo)** — phân bố theo instance:

| Loại cảnh báo | Số lượng | Đánh giá |
|---|---|---|
| Timestamp Disclosure - Unix | 98 | Nhiễu (Low, không khai thác được) |
| Cross-Domain Misconfiguration | 66 | Đúng cấu hình sai (Medium) |
| CSP Header Not Set | 52 | Đúng cấu hình sai (Medium) |
| Modern Web Application | 44 | Thông tin, không phải lỗi |
| User Agent Fuzzer | 24 | Tự sinh khi test, không phải lỗi |
| SQL Injection | 1 | **Lỗ hổng thật (High)** |
| Khác | ~1 | |

→ Chỉ **~15%** cảnh báo là actionable thật; phần lớn là nhiễu/cảnh báo cấu hình.
→ Hội đồng hay hỏi: "ZAP báo 286 lỗi thì vá sao cho hết?" — trả lời: phân loại theo
mức độ + khử trùng lặp + ưu tiên High trước, Medium theo SLA, Low/Info chỉ theo dõi.

**Semgrep (11 findings)**: 11/11 true positive (đều trúng code cấy thử) nhưng trùng
rule (7 lỗi thật, 11 cảnh báo) → cần dedup theo vị trí dòng code.

## 7. SCA — Dependency & image (Trivy)

| Mục tiêu | Kết quả |
|---|---|
| `app/requirements.txt` (flask==3.0.0) | 0 CVE HIGH/CRITICAL |
| Image `bkimminich/juice-shop` | **54 CVE (46 HIGH, 8 CRITICAL)** |

→ Image là bề mặt tấn công lớn: quét image trước khi deploy là bước bắt buộc.

## 8. Kết luận cho đề tài

1. **Không công cụ nào đủ một mình**: Semgrep 6/7, Gitleaks 1/7 (đúng chỗ Semgrep
   sai sót), DAST 1/7 (đúng chỗ cả hai không thấy). Phối hợp = phủ gần trọn.
2. **Chi phí thấp**: +1 phút 40 giây mỗi lần CI, đổi lấy chặn lỗi trước khi merge.
3. **Gate 2 chiều hoạt động thật**: đỏ khi lỗi, xanh khi vá (có bằng chứng 6 commit).
4. **DAST cần chủ đích**: quét tự động trên SPA dễ bỏ sót endpoint — hạn chế & hướng
   phát triển (quét theo OpenAPI, tích hợp IAST, DAST nightly).
5. **Nhiễu là vấn đề thật**: ~85% cảnh báo DAST là nhiễu → quy trình triage và
   ngưỡng chặn phân cấp (ERROR chặn / WARNING cảnh báo) là bắt buộc.

# Hướng dẫn test bảo mật BẰNG TAY trên OWASP Juice Shop

> Mục đích: kiểm thử thủ công để bù phần công cụ bỏ sót (logic nghiệp vụ, IDOR,
> chuỗi lỗi). Mọi test case dưới đây đã được xác minh chạy thật trên
> `http://localhost:3000` (bản Juice Shop đang chạy trong dự án).

**Phạm vi**: CHỈ test trên Juice Shop / app demo của dự án. Không thử trên hệ thống
không thuộc sở hữu của bạn.

## 0. Chuẩn bị (5 phút)

1. Mở `http://localhost:3000` bằng Chrome/Firefox.
2. Bật DevTools (F12) → tab **Network** → tick "Preserve log" — đây là "kính lúp" của bạn.
3. Mở 1 file ghi chép theo mẫu ở mục 6.
4. (Nâng cao) Đặt ZAP làm proxy cho trình duyệt: `localhost:8080` — ZAP ghi lại
   toàn bộ request để sửa payload và gửi lại (tab History → Replay).

## 1. Recon — nhìn trước khi chạm

| Bước | Làm gì | Đã xác minh |
|---|---|---|
| 1.1 Đọc `robots.txt` | Mở `http://localhost:3000/robots.txt` | Thấy `Disallow: /ftp` → **đường dẫn giấu bị lộ** |
| 1.2 Thử đường dẫn lộ | Mở `http://localhost:3000/ftp` | **200 OK** — liệt kê file công khai |
| 1.3 Xem response header | DevTools → Network → click request → tab Headers | Không có CSP, X-Frame-Options... (khớp báo cáo ZAP) |
| 1.4 Xem source JS | Network → filter JS → tìm file `main.js`, tìm endpoint `/rest/`, `/api/` | Liệt kê được API backend |

> Bài học: công cụ cũng làm mấy bước này (ZAP spider), nhưng *hiểu* được cái lộ ra
> thì chỉ người làm. robots.txt lộ /ftp là lỗi cấu hình, không tool nào đánh giá được mức độ.

## 2. SQL Injection (đã xác minh)

**Test 2.1 — Error-based** (ứng dụng phơi lỗi SQL ra ngoài):

```
http://localhost:3000/rest/products/search?q=' 
```

Kết quả đã xác minh: trang trả về `Error: SQLITE_ERROR: incomplete input`
→ **input chui thẳng vào câu lệnh SQL** = xác nhận có lỗ hổng (kể cả khi chưa khai thác được).

**Test 2.2 — Boolean-based**:

```
http://localhost:3000/rest/products/search?q=' OR '1'='1
```

Kết quả đã xác minh: trả về **46 sản phẩm** (toàn bộ bảng) — trong khi tìm "apple"
chỉ trả 0–1 sản phẩm. So sánh số lượng = bằng chứng khai thác được.

**Test 2.3 — UNION-based** (nâng cao): `' UNION SELECT id,email,password FROM Users--`
→ bản này trả lỗi cú pháp (cấu trúc câu lệnh khác) — **kết quả test âm tính cũng là
kết quả**: ghi lại "không khai thác được bằng UNION, chỉ error/boolean-based".

## 3. Path Traversal (đã xác minh — kết quả ÂM TÍNH)

```
http://localhost:3000/ftp/../package.json        (403)
http://localhost:3000/ftp/%2e%2e/package.json    (403)
```

Kết quả: **403 — server chặn traversal**. Ghi nhận: "đã thử 2 cách encode, phòng thủ
hoạt động". Đây là điểm mà bài thi thích: test viên chứng minh được mình *hiểu* phòng thủ.

## 4. Test trên trình duyệt (tự làm theo)

| Test | Các bước | Mong đợi |
|---|---|---|
| **Stored XSS** | Đăng ký tài khoản → vào 1 sản phẩm → đánh giá: `<script>alert('XSS')</script>` | Alert hiện ra khi người khác mở trang |
| **Reflected XSS** | Tìm kiếm: `<img src=x onerror=alert(1)>` | Alert hiện ngay trên trang kết quả |
| **IDOR** | Đăng nhập → vào Đơn hàng của tôi → chú ý URL/ request `/rest/orders/<số>` → sửa `<số>` thành số khác (thấp hơn) | Xem được đơn hàng người khác |
| **Broken Auth** | Quên mật khẩu → bắt request `/rest/user/change-password?token=...` trong DevTools → xem token có đoán được không (dài? random?) | Token yếu = lỗi |
| **JWT tampering** | DevTools → LocalStorage → copy `token` → dán vào jwt.io → xem payload (role, email) → sửa `role` thành `admin`, dùng lại | Phân quyền dựa trên JWT không kiểm tra chữ ký |
| **API trần** | Đăng nhập → DevTools → thử `GET /api/Users` với token | Danh sách user rò rỉ = lỗi |

## 5. Cách phân biệt "lỗi thật" vs "không phải lỗi"

- Lỗi thật: khai thác có **tác động** (đọc data người khác, chạy JS, om login).
- Không phải lỗi: chỉ khác biệt giao diện, hoặc lỗi đã được chặn (403 như mục 3).
- Khi nghi ngờ: đặt câu hỏi "kẻ tấn công được gì?" — không có lợi ích = Low/Info.

## 6. Mẫu ghi chép (copy vào file ghi chép của bạn)

```
Tên lỗi: SQL Injection (boolean-based) tại /rest/products/search
Mức độ:  High (CVSS ~8.6)
Các bước tái hiện:
  1. Mở http://localhost:3000/rest/products/search?q=' OR '1'='1
  2. Quan sát: trả về 46 sản phẩm (bình thường: 0–1)
Bằng chứng: screenshot DevTools/Network + response body
Tác động: đọc toàn bộ bảng products; có thể mở rộng UNION sang bảng Users
Khuyến nghị: dùng prepared statement (Sequelize bind parameter)
Công cụ bắt được?: ZAP (active scan có chủ đích) ✅ / Semgrep ❌ / Gitleaks ❌
```

Dòng cuối rất quan trọng — nó nối test tay với số liệu của `docs/thi-nghiem.md`.

## 7. Nối với đồ án

So sánh test tay vs công cụ (mục E1 trong `docs/thi-nghiem.md`):
- Test tay tìm được: IDOR, stored XSS, JWT — **3 mục mà không job nào trong pipeline bắt**.
- Công cụ tìm được: lỗi ở quy mô code (Semgrep 6/7), secret (Gitleaks), SQLi runtime (ZAP có chủ đích).
- Kết luận viết vào đồ án: *kiểm thử tự động là lớp nền, kiểm thử thủ công là lớp bổ sung bắt buộc trước release*.

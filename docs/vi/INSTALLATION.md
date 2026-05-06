# 🚀 Bắt đầu nhanh - DocuMind

<div align="right">
  🌍 <b><a href="../en/INSTALLATION.md">English Version</a></b>
</div>

## <a name="introduction"></a>📖 Giới thiệu

**DocuMind** là trợ lý hỗ trợ bởi AI giúp các nhà nghiên cứu và sinh viên xử lý tài liệu tiếng Việt một cách dễ dàng. Bằng cách kết hợp khả năng trích xuất tiên tiến của Docling với các mô hình LLM hàng đầu, chúng tôi cung cấp một nền tảng thống nhất để tóm tắt và tương tác với tài liệu.

---

## <a name="quick-start"></a>⚡ Bắt đầu nhanh

Để chạy DocuMind trong chưa đầy 5 phút:
1. Đảm bảo đã cài đặt `uv` và `Flutter`.
2. Chạy `uv sync` trong thư mục gốc.
3. Chạy `uv run python tests/test_docling_processor.py` để khởi động các model.
4. Chạy `uv run python backend/main.py`.

---

## <a name="installation"></a>🔧 Cài đặt

### Thiết lập Backend
1. **Môi trường Python:** Sử dụng `uv` để quản lý thư viện đồng nhất.
   ```bash
   uv sync
   ```
2. **AI Models:** Các model được tải động từ thư mục `ai/results/models`.

### Thiết lập Mobile
1. **Vào thư mục mobile:** `cd mobile`
2. **Cài đặt thư viện:** `flutter pub get`
3. **Chạy:** `flutter run`

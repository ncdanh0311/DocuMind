# Giai đoạn 2 — pipeline tài liệu, QA và tóm tắt

Cập nhật: 2026-11-05. Đã triển khai mã và kiểm thử kỹ thuật. **Chưa nghiệm thu chất lượng của bốn model thực tế:** chưa tìm thấy checkpoint đã fine-tune và chưa có corpus được gán nhãn để benchmark.

## Phần đã triển khai

| Hạng mục | Hành vi hiện tại |
| --- | --- |
| Artifact AI | Import bundle offline, giữ tokenizer/config/adapter/base và SHA-256; kiểm tra vocabulary, QA head và forward trước khi công bố. Không tải model khi import API. Bốn model vẫn là `phobert_qa`, `xlmroberta_qa`, `vit5`, `bartpho`. Embedding/reranker là hai bundle riêng. |
| Khả năng phục vụ | `GET /api/v1/capabilities` trả trạng thái từng model. QA thiếu ngưỡng hiệu chỉnh chưa được đánh dấu sẵn sàng. Web/mobile vô hiệu hóa lựa chọn chưa sẵn sàng. |
| Ingestion | Lưu file và enqueue, worker riêng trích xuất canonical text. Giữ Docling item provenance, mục, trang đầu/cuối thực tế; DOCX/TXT có trang `null`. Chunk có thứ tự toàn tài liệu, phiên bản và offset ký tự Unicode dạng `[start, end)`. |
| Chia đoạn | Dùng tokenizer của bundle, tính cả tiền xử lý/prefix/special token. Embedding tối đa 16 đoạn/lượt, kiểm tra 384 chiều và số hữu hạn. Không thay giới hạn token bằng số ký tự. |
| Hàng đợi | PostgreSQL `FOR UPDATE SKIP LOCKED`, lease 120 giây, heartbeat 30 giây, tối đa 3 lần nhận; lỗi tạm thời thử lại sau 10/30 giây. Token lease chặn worker cũ ghi kết quả. Transaction không kéo dài qua inference của worker. |
| Tính nhất quán | Version/chunks được công bố trong một transaction. Xóa/thay nguồn hủy job liên quan. Retry không tạo trùng version/chunk; tổng hợp dùng snapshot nguồn và cache key có model/pipeline version. |
| QA | Top 20 cosine theo đúng embedding version → rerank 3 → QA từng passage với cửa sổ trượt. PhoBERT căn chỉnh từ đã tách về ký tự nguồn. Không đoán nguồn bằng tìm chuỗi. `no_answer` không có citation. Lưu lịch sử, model version và span nguồn. |
| Tóm tắt | Từng phần → mục → tài liệu → sổ tay. Đọc hết input, không cắt 800 từ hoặc âm thầm truncate 512 token. Lưu các phần đã xử lý; không công bố bản tóm tắt chưa hoàn tất. |
| Client | POST tóm tắt trả 202 + summary/job ID; cache hoàn tất trả 200; còn tài liệu chưa sẵn sàng trả 409. Poll 3 giây, dừng khi hoàn tất/rời màn hình, lưu ID để mở lại; không hiển thị nội dung cache khi snapshot đã cũ. Mobile đã bỏ nội dung tóm tắt/keyword minh họa khỏi kết quả thật. |
| Xem nguồn | Mở trích dẫn trên web/mobile tải đúng version/span qua API có kiểm tra chủ sở hữu. Đây là đoạn nguồn canonical; trình xem toàn bộ PDF nằm ngoài đợt này. |
| Train/eval | Khôi phục `ai/src/data` và loại khỏi ignore dữ liệu. Giới hạn QA theo cấu hình model; EM/F1 tính trên text và gộp overflow windows; đánh giá test riêng. Eval summary nạp adapter đã lưu thay vì bọc LoRA lần nữa. ROUGE dùng từ Unicode, không tokenizer ASCII/stemming tiếng Anh. |

PDF scan không có text trả `ERR_DOCUMENT_NEEDS_OCR`. OCR nâng cao chưa nằm trong phạm vi này. Worker giới hạn mỗi lượt xử lý bằng `JOB_MAX_SECONDS=1800`; kết quả sau timeout/lease mất hiệu lực không được công bố. Hệ thống không cưỡng bức ngắt kernel GPU đang chạy.

## Chạy từ thư mục gốc project

Giữ `.env` với secret riêng hợp lệ và PostgreSQL có extension `vector`. Các kiểm thử đợt này chỉ dùng database riêng `documind_phase1_test`; chưa migrate database thật.

```powershell
uv sync --frozen
uv run --no-sync alembic upgrade head
uv run --no-sync uvicorn backend.main:app --host 127.0.0.1 --port 8000
# Hai cửa sổ terminal khác:
uv run --no-sync python -m ai.main
uv run --no-sync python -m backend.worker
```

`python -m backend.worker --once` nhận tối đa một job rồi thoát. API không còn dùng `BackgroundTasks` để chạy pipeline dài. Compose có service `worker` riêng, dùng chung upload volume với backend; Docker là một lựa chọn triển khai, không phải yêu cầu bắt buộc để chạy ứng dụng.

Sau nâng cấp schema từ giai đoạn 1, tài liệu cũ được đánh dấu `ERR_REPROCESS_REQUIRED`. Dùng nút **Xử lý lại** hoặc `POST /api/v1/documents/{id}/reprocess`; cần file nguồn còn trên đĩa. Version nguồn cũ của pipeline mới vẫn được giữ để truy xuất các trích dẫn đã lưu.

## Import checkpoint đã có

Source hiện chỉ khai báo checkpoint trong cấu hình; không tìm thấy bốn bộ weights tương ứng trong workspace. Cache `multilingual-e5-small` được tìm thấy nhưng có file liên kết Windows không truy cập được, nên chưa được dùng như bundle đã kiểm chứng. Không thay checkpoint QA đã fine-tune bằng model nền.

Mỗi source cần có tokenizer đi kèm và weights. Ví dụ với **đường dẫn thực của bạn**, chạy từ gốc repository:

```powershell
uv run --no-sync python -m ai.import_model --model phobert_qa --source D:/Checkpoints/phobert_qa/best_model
uv run --no-sync python -m ai.import_model --model xlmroberta_qa --source D:/Checkpoints/xlmroberta_qa/best_model
uv run --no-sync python -m ai.import_model --model vit5 --source D:/Checkpoints/vit5/best --base-source D:/Checkpoints/vit5-base
uv run --no-sync python -m ai.import_model --model bartpho --source D:/Checkpoints/bartpho/best --base-source D:/Checkpoints/bartpho-word-base
uv run --no-sync python -m ai.import_model --model embedding --source D:/Checkpoints/multilingual-e5-small
uv run --no-sync python -m ai.import_model --model reranker --source D:/Checkpoints/reranker
```

Chỉ dùng `--base-source` khi checkpoint là adapter; phải là đúng base local đã dùng khi train. Bundle đích mặc định là `ai/artifacts/{model_id}` (đã ignore). Không ghi đè bundle đang có. `--qa-threshold` chỉ dành cho ngưỡng đã hiệu chỉnh và có bằng chứng đánh giá; không chọn ngưỡng tùy ý để làm model chuyển sang trạng thái sẵn sàng. Cách chạy benchmark và cập nhật threshold được mô tả bên dưới.

## Benchmark và nghiệm thu còn lại

Runner: `python -m ai.benchmark`. Dataset JSON dùng canonical text, không dùng offset byte hay UTF-16:

```json
{
  "documents": [
    {"id": "doc-dev-01", "split": "dev", "text": "Hà Nội là thủ đô.", "summary_reference": "Hà Nội là thủ đô."}
  ],
  "questions": [
    {"id": "q-dev-001", "split": "dev", "document_id": "doc-dev-01", "question": "Thủ đô là gì?", "answers": [{"text": "Hà Nội", "start": 0, "end": 6}]}
  ]
}
```

Đây chỉ là ví dụ cấu trúc, **không phải bộ đánh giá hợp lệ**. Corpus thật phải có ít nhất 24 tài liệu, đúng 240 câu hỏi: mỗi split dev/test có 80 câu có đáp án và 40 câu không có đáp án. Câu không có đáp án dùng `answers: []`. Tài liệu của hai split phải tách biệt; runner chặn cả nội dung trùng giữa dev/test. Người biên soạn cần kiểm tra thêm rò rỉ với dữ liệu train và xác nhận câu không có đáp án trên toàn corpus của split.

```powershell
uv run --no-sync python -m ai.benchmark --dataset D:/Evaluation/documind.json --output ai/results/benchmark/validation.json --validate-only
uv run --no-sync python -m ai.benchmark --dataset D:/Evaluation/documind.json --output ai/results/benchmark/report.json --calibrate
```

`--calibrate` chọn threshold chỉ từ dev với tỷ lệ trả lời ở câu không có đáp án tối đa 5%, rồi dùng threshold đó cho test và cập nhật manifest QA. Báo cáo lưu checksum dataset, model versions, dự đoán/span, Recall@20/3, EM/F1, no-answer accuracy, false-positive rate, source accuracy, p50/p95 và bộ nhớ. Các điểm QA/ROUGE trong benchmark nằm trong khoảng 0–1; metric của Trainer nằm trong khoảng 0–100.

Độ trễ đo offline retrieval/rerank/QA, không gồm mạng HTTP và chờ queue; lượt đầu có thể gồm cold load. Summary đo ROUGE theo từng tài liệu có `summary_reference`, kèm rubric factuality/coverage/readability để người đọc chấm. Chưa có điểm benchmark, nhãn 240 câu hay điểm rubric thật được tạo ra trong đợt này. Chưa chạy fine-tune lại. Để dùng script train/eval với dữ liệu Hugging Face local, cài thêm `uv sync --frozen --group research`; đường dẫn trong cấu hình được chuẩn hóa tương đối với thư mục `ai/`.

## Kiểm thử

Các lệnh kiểm thử database luôn yêu cầu `TEST_DATABASE_URL` trỏ tới PostgreSQL riêng có tên kết thúc bằng `_test`:

```powershell
$env:TEST_DATABASE_URL='postgresql://postgres:phase1-test@127.0.0.1:55432/documind_phase1_test'
uv run --no-sync pytest
# Thêm kiểm thử runtime bằng model nhỏ tạo cục bộ, không tải checkpoint:
uv run --no-sync pytest tests/inference
```

Các bài kiểm thử bao gồm claim cạnh tranh, lease hết hạn/fencing, retry/timeout, xóa nguồn trong lúc inference, không publish dở dang, đóng transaction khi inference, cache/staleness, phân quyền source/job/summary, nâng/hạ migration và đồng bộ metadata. Runtime fixtures kiểm tra forward/overflow/abstention, từ chối base model thiếu QA head, căn chỉnh PyVi và provenance DOCX thật. Các fixture weights ngẫu nhiên chỉ dùng kiểm tra kỹ thuật, không chứng minh chất lượng model.

Web: `npm test`, `npx tsc --noEmit`, `npm run lint`, `npm run build`. Mobile: `flutter test --no-pub`, `flutter analyze --no-pub --no-fatal-infos`. Các cảnh báo INFO/deprecation của SDK/thư viện được ghi riêng, không tính thành kết quả benchmark.

## Kết quả xác minh tại máy phát triển

- Python: **61 bài qua** trên database PostgreSQL 16/pgvector kiểm thử riêng, bao gồm 4 bài runtime/offline và DOCX.
- Web: **11 bài qua**; TypeScript, ESLint và production build Webpack qua.
- Mobile: **14 bài qua**; analyzer không có ERROR/WARNING, còn 6 mục INFO/lint.
- `alembic check`: không có khác biệt schema; `docker compose config --quiet`, `uv lock --check --offline` và AST Python qua.
- Chưa chạy benchmark bằng checkpoint/corpus thật, SMTP thật, build APK hoặc GitHub Actions remote. Không thay đổi `.env` và không migrate database thật.

## Lỗi Docker trong lúc kiểm thử

Docker Desktop gặp `ERROR_CANT_ACCESS_FILE (1920)` ở socket `dockerInference`. Đã kiểm tra log và đổi tên hai thư mục runtime lỗi sang bản sao lưu `run.backup-20261105-112822` và `docker-secrets-engine.backup-20261105-112822`; Docker sau đó khởi động và database kiểm thử chạy được. Không factory reset và không xóa volume/database. Đây là lỗi môi trường Docker Desktop, tách biệt với lỗi ứng dụng. Docker được tắt lại sau kiểm thử theo yêu cầu của bạn.

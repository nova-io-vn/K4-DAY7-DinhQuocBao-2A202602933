# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đinh Quốc Bảo

**Nhóm:** Aura

**Ngày:** 19/09/2026

**Chủ đề thực nghiệm:** Học phí đại học

> Báo cáo này chỉ trình bày phần làm việc cá nhân. Nội dung báo cáo nhóm không được chỉnh sửa.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Hai đoạn văn bản có cosine similarity cao khi vector của chúng hướng gần giống nhau, thường thể hiện hai đoạn có nội dung hoặc ý nghĩa tương tự. Điểm càng gần 1 thì mức tương đồng càng cao; gần 0 thường cho thấy ít liên quan.

**Ví dụ có độ tương tự CAO:**

- Câu A: “Sinh viên đóng học phí theo số tín chỉ đã đăng ký.”
- Câu B: “Học phí của sinh viên được tính theo tín chỉ đăng ký.”
- Tại sao tương đồng: Hai câu cùng mô tả cách tính học phí dựa trên số tín chỉ đăng ký, chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**

- Câu A: “Học phí chương trình thạc sĩ được tính theo tháng.”
- Câu B: “Thư viện cho sinh viên mượn sách trong hai tuần.”
- Tại sao khác: Hai câu thuộc hai dịch vụ khác nhau và không chia sẻ ý nghĩa chính.

**Tại sao cosine similarity được ưu tiên hơn khoảng cách Euclid cho text embeddings?**

Cosine similarity so sánh hướng của vector nên tập trung vào mẫu ngữ nghĩa, ít bị ảnh hưởng bởi độ lớn vector hay độ dài văn bản. Khoảng cách Euclid phụ thuộc trực tiếp vào độ lớn nên hai vector cùng hướng nhưng khác chuẩn vẫn có thể bị đánh giá là xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:**

`ceil((10.000 - 50) / (500 - 50)) = ceil(9.950 / 450) = ceil(22,11) = 23 chunks`.

**Nếu `overlap` tăng lên 100:**

`ceil((10.000 - 100) / (500 - 100)) = ceil(9.900 / 400) = ceil(24,75) = 25 chunks`.

Số chunk tăng từ 23 lên 25 vì bước dịch giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giúp giữ ngữ cảnh nằm sát ranh giới chunk, nhưng làm tăng dữ liệu trùng lặp, chi phí nhúng và dung lượng lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`:**

Tôi dùng biểu thức chính quy `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng hoặc xuống dòng đứng sau dấu kết thúc câu, đồng thời giữ dấu câu trong nội dung. Các câu được loại khoảng trắng thừa rồi gom theo `max_sentences_per_chunk`; văn bản rỗng hoặc chỉ có khoảng trắng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`:**

Thuật toán thử lần lượt các separator `\n\n`, `\n`, `. `, khoảng trắng và chuỗi rỗng. Các phần nhỏ được ghép lại nếu chưa vượt `chunk_size`; phần quá lớn được tách đệ quy bằng separator ưu tiên thấp hơn. Base case là đoạn đã không vượt kích thước; nếu hết separator thì cắt cứng theo số ký tự để luôn kết thúc an toàn.

### Lớp EmbeddingStore

**`add_documents` + `search`:**

Mỗi `Document` được chuẩn hóa thành record gồm ID duy nhất, nội dung, bản sao metadata có thêm `doc_id`, và embedding. Chế độ in-memory tính tích vô hướng giữa embedding truy vấn và embedding đã lưu, sắp xếp điểm giảm dần rồi lấy `top_k`; nếu có ChromaDB thì dùng collection tương ứng.

**`search_with_filter` + `delete_document`:**

Metadata được lọc trước khi tính similarity để giảm nhiễu và tránh xếp hạng các tài liệu sai trường/đối tượng. `delete_document` xóa toàn bộ record có `metadata["doc_id"]` trùng ID yêu cầu và trả về `True` chỉ khi thực sự có record bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`:**

Agent lấy top-k chunk (có thể kèm `metadata_filter`), ghép thành phần `NGỮ CẢNH` có nhãn nguồn và `doc_id`, sau đó đặt câu hỏi ở phần riêng. Prompt yêu cầu chỉ dùng dữ liệu trong ngữ cảnh và phải nói rõ khi thiếu thông tin nhằm hạn chế câu trả lời không có căn cứ.

### Cấu hình thực nghiệm cá nhân

Tôi dùng `RecursiveChunker(chunk_size=1400)` trên 6 file trong `data/hoc_phi`, tạo 34 chunk. Vì backend mock mặc định tạo vector giả ngẫu nhiên và máy không cài mô hình ngoài, benchmark dùng bộ nhúng từ vựng unigram/bigram băm cục bộ 4.096 chiều trong `scripts/run_individual_evaluation.py`; đây là cấu hình offline, tất định và không cần API key. Metadata `audience`, `institution`, `category`, `language` được bổ sung lúc ingest, không sửa các file dữ liệu dùng chung.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Đã hoàn thiện toàn bộ TODO trong `src/chunking.py`, `src/store.py` và `src/agent.py`.

### Kết quả kiểm thử

```text
> .\.venv\Scripts\python.exe -m pytest tests -v
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
collected 42 items

tests/test_solution.py ..........................................       [100%]

============================== 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua:** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các điểm dưới đây được tính bằng `compute_similarity()` trên vector của bộ nhúng từ vựng cục bộ. Trong thực nghiệm này, tôi quy ước điểm từ 0,30 trở lên là “cao”.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Sinh viên đóng học phí theo số tín chỉ đã đăng ký. | Học phí của sinh viên được tính theo tín chỉ đăng ký. | Cao | 0,6008 | Có |
| 2 | Học lại chương trình chuẩn có mức thu 840.000 đồng một tín chỉ. | Sinh viên học cải thiện hệ chuẩn nộp 840.000 đồng mỗi tín chỉ. | Cao | 0,4013 | Có |
| 3 | Học phí chương trình thạc sĩ được tính theo tháng. | Thư viện cho sinh viên mượn sách trong hai tuần. | Thấp | 0,0000 | Có |
| 4 | Sinh viên thanh toán học phí bằng cách quét mã QR. | Người học dùng ứng dụng ngân hàng quét mã QR để nộp tiền. | Cao | 0,2837 | Không |
| 5 | Nhà trường trích quỹ để cấp học bổng cho sinh viên. | Lớp học lại dưới bốn sinh viên phải đóng học phí cao hơn. | Thấp | 0,2208 | Có |

**Kết quả bất ngờ nhất:**

Cặp 4 có cùng hành động “quét mã QR” nhưng chỉ đạt 0,2837, thấp hơn ngưỡng dự đoán. Điều này cho thấy bộ nhúng từ vựng đơn giản phụ thuộc nhiều vào từ trùng khớp và không hiểu tốt các cặp diễn đạt tương đương như “thanh toán học phí” với “nộp tiền”; mô hình embedding ngữ nghĩa đa ngữ sẽ phù hợp hơn cho hệ thống thật.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Lệnh tái lập kết quả:

```powershell
.\.venv\Scripts\python.exe scripts\run_individual_evaluation.py
```

| # | Câu hỏi (Query) | Top-1 chunk truy xuất được (tóm tắt) | Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---:|---|---|---:|---|---|
| 1 | Học lại hoặc học cải thiện chương trình chuẩn thu bao nhiêu một tín chỉ? | Thông báo 731/TB-HVTC về học lại, cải thiện và học kỳ phụ, chunk 0. Đoạn chứa mức cụ thể ở top-2. | 0,4019 | Có một phần; đáp án ở top-2 | Chương trình chuẩn và các hệ được liệt kê thu **840.000 đồng/tín chỉ**. |
| 2 | Thu học phí học kỳ phụ năm học 2025-2026 từ ngày nào đến hết ngày nào? | Phần mở đầu Thông báo 731/TB-HVTC, chunk 0. Đoạn thời gian ở top-2. | 0,4766 | Có một phần; đáp án ở top-2 | Thu từ **23/05/2026 đến hết 01/06/2026**. |
| 3 | Lớp học lại có dưới 4 sinh viên phải đóng mức nào? | Mục 8 thông báo học phí 2026-2027 của UTT, chunk 3. | 0,3355 | Có | Thu bằng **2,5 lần** học phí hiện hành của học phần học kỳ chính. |
| 4 | Sinh viên quốc tế không phải diện hiệp định có mức thu mỗi năm học là bao nhiêu? | Mục 1.2 báo cáo lộ trình học phí USSH, chunk 2. | 0,3347 | Có | **45.000.000 đồng/năm học/sinh viên**, thu theo năm học. |
| 5 | Hằng năm nhà trường trích khoảng bao nhiêu cho Quỹ học bổng? | Mục 9 thông báo học phí UTT, chunk 3. | 0,2804 | Có | Nhà trường trích khoảng **30 tỷ đồng** cho Quỹ học bổng. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

### Metadata filter đã dùng

- Câu 1: `{"audience": "student", "institution": "HVTC"}`.
- Câu 2: `{"institution": "HVTC"}`.
- Câu 3 và 5: `{"institution": "UTT"}`.
- Câu 4: `{"institution": "USSH"}`.

Lọc theo trường/đối tượng giúp loại các thông báo có từ khóa “học phí” nhưng thuộc cơ sở khác. Tuy nhiên, dữ liệu crawl còn phần đầu trang và điều hướng lặp lại, khiến câu 1 và 2 trả phần mở đầu ở top-1 trong khi chunk có con số đứng top-2. Nếu cải thiện tiếp, tôi sẽ làm sạch boilerplate và chia theo tiêu đề/mục để phần tiêu đề cùng nằm trong chunk chứa nội dung chi tiết.

**Điều học được từ demo/so sánh:**

Chưa có kết quả của thành viên khác trong `REPORT_NHOM.md`, nên tôi không suy đoán hoặc tự tạo nhận xét thay cho nhóm. Từ thử nghiệm cá nhân, bài học rõ nhất là metadata theo `institution` tăng precision đáng kể, còn kích thước chunk lớn giữ được điều khoản và con số nhưng dễ mang theo nội dung thừa.

---

## Tự đánh giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |

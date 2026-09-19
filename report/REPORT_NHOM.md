# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Aura (K4-L3A)
**Thành viên:** 
- Nguyễn Thu Hằng - 2A202602463
- Đậu Văn Thạch - 2A202602592
- Đinh Quốc Bảo - 2A202602933 
- Lê Thanh Tùng - 2A202602499

**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học phí đại học Việt Nam — mức thu theo tín chỉ/tháng, học phí học lại, khung học phí theo Nghị định 238/2025/NĐ-CP.

**Tại sao nhóm chọn chủ đề này?**
> Học phí là thông tin được sinh viên, phụ huynh và nhân viên tài vụ tra cứu thường xuyên nhất, và hầu hết trường đại học Việt Nam đều công khai trên website nên thu thập được hợp lệ, minh bạch. Về kỹ thuật, đây là chủ đề lý tưởng để đo retrieval: văn bản soạn theo điều khoản đánh số nên có cấu trúc rõ để chunk; câu trả lời hầu hết là **một con số cụ thể** nên kiểm chứng được bằng chuỗi ký tự thay vì đánh giá cảm tính. Quan trọng nhất, cùng một câu hỏi có đáp án khác nhau theo đối tượng và theo bậc học — đúng thứ cần để chứng minh metadata filter có giá trị thật.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Lộ trình thu học phí **bậc đại học** 2026-2027 (USSH – ĐHQGHN) | `ussh.vnu.edu.vn/vi/gioi-thieu/ba-cong-khai/bao-cao-lo-trinh-thu-hoc-phi-cac-he-nam-hoc-2026-2027-19718.html` | 2026-09-19 / 2026-05-26 | 7.204 | audience=**student**, level=**undergraduate**, university=ussh-vnu, department=finance, category=tuition-rate, language=vi |
| 2 | Lộ trình thu học phí **bậc sau đại học** 2026-2027 (USSH – ĐHQGHN) | *(cùng URL trên — tách file theo bậc học)* | 2026-09-19 / 2026-05-26 | 2.676 | audience=student, level=**postgraduate**, university=ussh-vnu, department=finance, category=tuition-rate, language=vi |
| 3 | Thông báo mức thu học phí 2026-2027 (ĐH Công nghệ GTVT) | `www.utt.edu.vn/vn/daotao/thong-bao/thong-bao-muc-thu-hoc-phi-nam-hoc-2026-2027-a17279.html` | 2026-09-19 / 2026-07-21 | 6.062 | audience=student, level=undergraduate, university=utt, department=finance, category=tuition-rate, language=vi |
| 4 | Thu học phí học lại/cải thiện/học bù kỳ phụ 2025-2026 (Học viện Tài chính) | `hvtc.edu.vn/TB-Ve-viec-thu-hoc-phi-hoc-lai-hoc-cai-thien-diem-hoc-bu-Hoc-ky-phu-nam-hoc-2025--2026-doi-voi-sinh-vien-cac-he-dao-tao-_34041.html` | 2026-09-19 / **731/TB-HVTC ngày 18/05/2026** | 3.270 | audience=student, level=undergraduate, university=hvtc, department=finance, category=**tuition-retake**, language=vi |
| 5 | Khung học phí từ 2025-2026 theo Nghị định 238/2025/NĐ-CP (ĐH Nha Trang đăng lại) | `phongkhtc.ntu.edu.vn/tin-tuc/quy-dinh-moi-nhat-ve-muc-hoc-phi-tu-nam-hoc-2025---2026` | 2026-09-19 / 2025-09-30 | 7.477 | audience=**all**, level=**any**, university=ntu, department=finance, category=**tuition-policy**, language=vi |

Crawl bằng `scripts/fetch_public_pages.py` từ 7 URL, ra 5 tài liệu. Ba nguồn bị loại: **HCMUAF** (server trả chứng chỉ SSL thiếu mắt xích trung gian → `CERTIFICATE_VERIFY_FAILED`; nhóm không tắt xác minh SSL để lách), **PNT** (trang chỉ có link tải PDF, text trích ra không chứa một con số học phí nào), **PTIT** (trang danh sách tin, mọi mục cắt cụt bằng `[…]`). Chi tiết: `data/hoc-phi/README.md`.

Tài liệu USSH được **tách làm 2 file** vì một trang gộp cả bậc đại học lẫn sau đại học với hai mức thu khác nhau — để nguyên một file thì `metadata_filter` không có gì để lọc.

Hai chỗ mất dữ liệu đã biết và nhóm không bịa để bù: bảng mức thu các khóa từ 75 trở đi của UTT, và các bảng mức sàn – mức trần của Nghị định 238 trong bài NTU — đều nằm trong bảng/ảnh HTML mà trình trích xuất text không đọc được. Cả hai được ghi chú ngay trong file, và benchmark query tránh hỏi vào phần đã mất.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ. *(Một số điện thoại cá nhân của cán bộ trong bản gốc HVTC đã được gỡ bỏ khi làm sạch.)*
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata. *(Chỉ HVTC có số hiệu thật; bốn tài liệu còn lại nguồn không nêu nên dùng ngày đăng — không bịa số hiệu.)*

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | enum | `student` / `all` | Tách thông báo cụ thể của trường khỏi bài về khung pháp lý. Bài khung pháp lý chỉ trả lời "VLVH không vượt quá 150% hệ chính quy" — đúng luật nhưng **không có con số**, tức câu trả lời sai loại với sinh viên đang hỏi phải đóng bao nhiêu |
| `level` | enum | `undergraduate` / `postgraduate` / `any` | Cùng câu hỏi "một tháng đóng bao nhiêu" có hai đáp án: đại học 1.910.000đ/tháng, thạc sĩ 2.865.000đ/tháng. Chiều lọc mạnh nhất của corpus này |
| `university` | enum | `ussh-vnu`, `utt`, `hvtc`, `ntu` | Corpus gom từ 4 trường nên mọi câu hỏi không nêu tên trường đều mơ hồ; trường này để sẵn cho vòng cải tiến tiếp theo |
| `category` | enum | `tuition-rate`, `tuition-retake`, `tuition-policy` | Phân biệt mức thu thường, học phí học lại và quy định khung — ba loại câu hỏi khác hẳn nhau |
| `doc_id` | string | `ussh-hoc-phi-dai-hoc-2026-2027` | Trỏ về **file gốc**, không phải id chunk. `delete_document()` xóa theo nó; benchmark đối chiếu theo nó |
| `chunk_index` / `chunk_total` | int | `2` / `9` | Biết chunk nằm ở đâu trong tài liệu — phục vụ truy vết nguồn và phân tích "đúng tài liệu, sai section" |
| `source_url` + `retrieved_at` + `document_version` | string | `2026-05-26` | Kiểm tra độ mới và truy vết câu trả lời về đúng bản văn bản |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu — lệnh `python bench.py --baseline`, `chunk_size=600`, đã bỏ frontmatter:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| ussh-hoc-phi-dai-hoc | FixedSizeChunker (`fixed_size`) | 10 | 589,5 | ✗ Chạm trần 600 → cắt giữa câu, bảng mức thu bị đứt |
| ussh-hoc-phi-dai-hoc | SentenceChunker (`by_sentences`) | 19 | 279,9 | ✓ Câu trọn vẹn nhưng vụn nhất (min 82) — bảng mức thu bị xé nhỏ |
| ussh-hoc-phi-dai-hoc | RecursiveChunker (`recursive`) | 11 | 485,0 | ✓ Cắt ở ranh giới đoạn, không chunk nào chạm trần (max 599) |
| ntu-khung-hoc-phi | FixedSizeChunker (`fixed_size`) | 10 | 575,9 | ✗ Chạm trần 600 |
| ntu-khung-hoc-phi | SentenceChunker (`by_sentences`) | 10 | 519,4 | ✓ Văn bản pháp lý câu dài nên không vụn |
| ntu-khung-hoc-phi | RecursiveChunker (`recursive`) | 12 | 433,1 | ✓ |
| hvtc-hoc-phi-hoc-lai | FixedSizeChunker (`fixed_size`) | 4 | 573,8 | ✗ Chạm trần 600 |
| hvtc-hoc-phi-hoc-lai | SentenceChunker (`by_sentences`) | 9 | 233,2 | ✓ nhưng vụn nhất corpus (min 72) |
| hvtc-hoc-phi-hoc-lai | RecursiveChunker (`recursive`) | 5 | 421,4 | ✓ |

Hai điều đọc được từ bảng. Thứ nhất, `fixed_size` chạm trần 600 ở **cả ba tài liệu** — dấu hiệu nó cắt theo vị trí ký tự bất kể nội dung. Thứ hai, `by_sentences` đổi hẳn tính chất theo thể loại văn bản: với văn bản pháp lý câu dài (NTU) nó cho chunk 519 ký tự, nhưng với thông báo nhiều dòng ngắn (USSH, HVTC) nó vụn xuống 233–280 — dấu hiệu sớm của vấn đề lộ ra ở mục 3.

Baseline của Thu Hằng chạy trên bản crawl thô (`chunk_size=200`) cho `recursive` **320 chunk dài trung bình 43 ký tự** — vụn hơn cả hai chiến lược kia. Với cài đặt trong repo này, `recursive` cho 5–12 chunk dài 421–485. Khác biệt nằm ở **bước gom (`_merge`)**: sau khi cắt theo separator, các mảnh nhỏ liền kề phải được nối lại tới sát `chunk_size`; thiếu bước đó, văn bản nhiều dòng ngắn sinh ra hàng trăm chunk vụn. Đây là bài học kỹ thuật cụ thể nhất khi ghép báo cáo — `RecursiveChunker` có hai chiều (đệ quy xuống + gom lên) và người ta thường chỉ viết một.

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Thu Hằng**
- **Loại chiến lược:** `FixedSizeChunker` (`chunk_size=500, overlap=50`)
- **Mô tả & lý do chọn cho chủ đề này:** Chia văn bản thành các đoạn 500 ký tự với 50 ký tự chồng lên nhau. Với tài liệu học phí chứa nhiều danh sách, con số và mệnh giá ngắn, chunk cố định đảm bảo kích thước đồng đều, dễ embed và so sánh. Overlap 50 ký tự giữ ngữ cảnh ở ranh giới, tránh mất thông tin số liệu quan trọng ở đầu/cuối chunk.
- **Code snippet (nếu custom):**
```python
chunker = FixedSizeChunker(chunk_size=500, overlap=50)
# 94 chunk từ 6 tài liệu crawl thô (~57.333 ký tự nội dung)
```

**Thành viên 2 — Đậu Văn Thạch**
- **Loại chiến lược:** `SentenceChunker` (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Nhận diện ranh giới câu bằng regex và gom tối đa 3 câu vào một chunk. Phù hợp với mảng học phí vì các quy định luôn được phát biểu thành từng câu hoàn chỉnh (thời hạn nộp, cú pháp chuyển khoản, mức phí). Cắt theo câu giữ trọn vẹn ngữ nghĩa từng quy định mà không bị đứt đoạn ngẫu nhiên giữa chừng như cắt theo ký tự cố định.
- **Code snippet (nếu custom):**
```python
raw_sentences = re.split(r'(?<=[.!?])(?:\s+|\n+)', text)
sentences = [s.strip() for s in raw_sentences if s.strip()]
for i in range(0, len(sentences), self.max_sentences_per_chunk):
    chunks.append(" ".join(sentences[i : i + self.max_sentences_per_chunk]).strip())
```

**Thành viên 3 — Đinh Quốc Bảo**
- **Loại chiến lược:** `RecursiveChunker` (`chunk_size=1400`, separator `\n\n`, `\n`, `. `, khoảng trắng, chuỗi rỗng)
- **Mô tả & lý do chọn:** Tài liệu học phí được tổ chức theo mục, đoạn và danh sách, trong đó **điều kiện áp dụng cần nằm gần mức tiền tương ứng**. `RecursiveChunker` ưu tiên giữ ranh giới đoạn/mục, chỉ dùng separator nhỏ hơn khi đoạn còn quá dài, nhờ đó hạn chế cắt rời tên đối tượng, mức thu và hình thức thu. Kích thước 1.400 ký tự giữ đủ ngữ cảnh cho các điều khoản dài.
- **Code snippet (nếu custom):**
```python
chunker = RecursiveChunker(separators=["\n\n", "\n", ". ", " ", ""], chunk_size=1400)
chunks = chunker.chunk(document.content)
```

**Thành viên 4 — Lê Thanh Tùng**
- **Loại chiến lược:** `HeadingChunker` (**custom**, `max_chunk_size=800, min_chunk_size=150`) — vai chunk theo tiêu đề/mục bắt buộc của K4-L3A
- **Mô tả & lý do chọn:** Văn bản học phí được **người soạn chia sẵn theo mục** (`## 7. Học phí lớp học lại, học cải thiện`). Mỗi mục là một đơn vị ngữ nghĩa tự chứa: nó nêu **cả điều kiện lẫn con số** trong cùng một khối. Tôn trọng ranh giới đó thì chunk vừa mạch lạc vừa map 1-1 với cách người dùng đặt câu hỏi — "lớp ít sinh viên thì tính thế nào" ≈ đúng một mục. Cùng trực giác mà Bảo diễn đạt ("điều kiện nằm gần mức tiền"), nhưng thay vì chọn `chunk_size` đủ lớn để *hy vọng* hai thứ rơi cùng chunk, chiến lược này **dùng thẳng ranh giới người soạn đã đánh dấu**.
- **Code snippet (nếu custom):**
```python
# (a) Section dài quá ngưỡng -> hạ xuống recursive VÀ gắn lại tiêu đề vào từng mảnh con.
#     Không có bước này, mảnh thứ hai trở đi mất ngữ cảnh "đây là mục nói về cái gì".
prefix = f"{heading}\n" if (self.keep_heading and heading) else ""
budget = max(50, self.max_chunk_size - len(prefix))
for sub_index, sub in enumerate(RecursiveChunker(chunk_size=budget).chunk(body)):
    chunks.append(sub if sub_index == 0 else f"{prefix}{sub}")

# (b) Gộp section quá ngắn. Trường hợp đặc biệt: một dòng heading đứng MỘT MÌNH
#     ("## 2. Học phí đối với giáo dục đại học (Điều 10)" — vì ngay dưới nó là "### 2.1")
#     thì gộp VÔ ĐIỀU KIỆN về phía sau, kể cả khi vượt ngưỡng: phần tràn tối đa chỉ
#     bằng chính độ dài tiêu đề, vẫn hơn là để một chunk rỗng nghĩa chiếm slot top-k.
if len(previous_body) < self.min_chunk_size:
    merged[-1] = (previous_heading or heading, f"{previous_body}\n\n{body}")
    continue
if len(body) < self.min_chunk_size and len(candidate) <= self.max_chunk_size:
    merged[-1] = (previous_heading or heading, candidate)
    continue
```
Chi tiết (b) đến từ đo thật: bản đầu cho 48 chunk với **min = 18 ký tự**; sau vòng gộp thứ nhất còn 41 chunk, min 48; xử lý tiếp trường hợp heading cụt mới còn **39 chunk, min 125**. Cột `min_length` trong output comparator là chỉ số chẩn đoán đáng nhìn — `count` và `avg_length` che mất hoàn toàn vấn đề này.

### So Sánh Giữa Các Thành Viên

Điểm dưới đây chạy **cùng corpus, cùng 5 câu hỏi mục 3, cùng `gemini-embedding-001`**, chỉ đổi dòng chọn chunker (`python bench.py --all`). Cột điểm là **mức nội dung** — mức doc_id ghi trong ngoặc để thấy khoảng thổi phồng.

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Thu Hằng | `FixedSizeChunker` (600/100) | **6**/10 *(doc_id 8/10)* · 40 chunk, TB 556 | Chunk dài nên phủ ngữ cảnh tốt nhất trên mỗi slot top-k; kích thước nhất quán, dễ tune | Cắt giữa câu. Làm hỏng Q1: chuỗi `530.000đ/tín chỉ` rơi đúng chỗ nối dù đã có overlap 100 |
| Đậu Văn Thạch | `SentenceChunker` (max 3 câu) | **6**/10 *(doc_id **10**/10)* · 54 chunk, TB 345 | Mọi chunk là câu trọn vẹn; **tìm đúng tài liệu ở hạng 1 cả 5 câu** | Chunk ngắn nhất corpus → đáp án hai vế bị xé làm đôi. Chênh **−4 điểm** giữa hai cách chấm, lớn nhất nhóm |
| Đinh Quốc Bảo | `RecursiveChunker` (600) | **6**/10 *(doc_id 8/10)* · 40 chunk, TB 467 | Không chunk nào chạm trần `chunk_size` → cắt ở ranh giới ngữ nghĩa thật. An toàn nhất khi corpus không có heading ổn định | Trượt Q2 và Q3; ranh giới đoạn `\n\n` vẫn tách mốc ngày khỏi ngữ cảnh |
| Lê Thanh Tùng | `HeadingChunker` (800/150) | **9**/10 *(doc_id 9/10)* · 39 chunk, TB 492 | **Chênh 0 giữa hai cách chấm** — chunk tự chứa đáp án chứ không chỉ nói về đáp án | Không có overlap: mỗi thông tin chỉ có đúng một cơ hội lọt top-k. Trượt hạng 1 ở Q2 |

*Ghi chú điều kiện đo:* ba bản báo cáo thành viên tự đo trên điều kiện khác nhau (Hằng: corpus crawl thô 6 file + `MockEmbedder` + bộ query riêng → tự báo 4/10; Bảo: bộ query riêng → tự báo 10/10; Thạch: chưa có số liệu). Ba con số đó **không so sánh được với nhau**, nên bảng trên dựng lại toàn bộ trên cùng một điều kiện. Cấu hình `chunk_size=1400` của Bảo chưa được đo ở đây — bảng dùng 600 theo mặc định repo; đây là thí nghiệm nhóm nên chạy trước demo.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **`HeadingChunker` — và điều đáng nói là hai cách chấm cho hai người thắng khác nhau.** Chấm theo `doc_id`, `SentenceChunker` thắng tuyệt đối 10/10: cả 5 câu đều lấy đúng tài liệu ở hạng 1. Chấm ở mức nội dung, nó rơi xuống 6/10 còn `HeadingChunker` lên 9/10. Nếu nhóm chỉ chấm mức `doc_id` thì sẽ mang một kết luận sai đi demo.
> Nguyên nhân rất cụ thể: `SentenceChunker` cắt thành 54 chunk ngắn (TB 345 ký tự), nên ở Q4 nó lấy đúng tài liệu UTT nhưng chunk chứa *"từ 4 sinh viên trở lên"* và chunk chứa *"dưới 4 sinh viên → 2,5 lần"* rơi vào **hai chunk khác nhau** — top-3 có tài liệu đúng mà không trả lời được câu hỏi. Đây đúng là điểm yếu Thạch dự đoán nhưng theo chiều ngược lại: anh kỳ vọng "mỗi quy định là một câu hoàn chỉnh", thực tế nhiều quy định học phí cần **hai câu** mới đủ — một câu nêu điều kiện, một câu nêu mức.
> `HeadingChunker` không dính lỗi này vì ranh giới chunk trùng với ranh giới người soạn văn bản đã chia. Bài học tổng quát: **với văn bản quy định, ranh giới ngữ nghĩa tốt nhất không phải thứ mình tính ra bằng số ký tự hay số câu — nó đã có sẵn trong tài liệu, việc của mình là đừng phá nó.**

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên các ngành khóa QH-2023 trở về trước đóng bao nhiêu tiền một tín chỉ? *(tra số liệu)* | **530.000đ/tín chỉ/hệ số**, thu theo tín chỉ đăng ký học (theo NĐ 238/2025) | `ussh-hoc-phi-dai-hoc-2026-2027` — mục 1.1 |
| 2 | Học phí một tín chỉ hệ vừa làm vừa học được tính như thế nào? *(**cần `metadata_filter={"audience":"student"}`**)* | USSH thu **700.000đ/tín chỉ** cho khóa QH-2023 trở về trước và các ngành "còn lại" của khóa sau; ngành đã kiểm định thu 880.000đ hoặc 1.050.000đ/tín chỉ | `ussh-hoc-phi-dai-hoc-2026-2027` — mục 3 |
| 3 | Thời gian nộp học phí học lại học kỳ phụ năm học 2025-2026 là khi nào? *(tra mốc thời gian)* | Từ ngày **23/05/2026 đến hết ngày 01/06/2026** (TB 731/TB-HVTC) | `hvtc-hoc-phi-hoc-lai-ky-phu-2025-2026` — mục 2 |
| 4 | Lớp học phần học lại có ít sinh viên đăng ký thì học phí tính thế nào? *(hỏi điều kiện/ngưỡng)* | Từ **4 sinh viên** trở lên: bằng mức học phí hiện hành. **Dưới 4 sinh viên**: bằng **2,5 lần** mức hiện hành | `utt-muc-thu-hoc-phi-2026-2027` — mục 7 |
| 5 | Mức thu học phí một tháng cho một người học là bao nhiêu? *(**cần `metadata_filter={"level":"postgraduate"}`**)* | Thạc sĩ **2.865.000đ/tháng/HV** (2.685.000đ với Quản trị Văn phòng, Khoa học Quản lý); tiến sĩ 4.775.000đ/tháng/NCS. Bậc đại học là mức khác (1.910.000đ/tháng/SV) | `ussh-hoc-phi-sau-dai-hoc-2026-2027` — mục 1.1 |

Hai câu được thiết kế để **bắt buộc phải lọc**. Q2 không nêu người hỏi là ai, trong khi corpus có tài liệu `audience=all` (bài Nghị định 238) dùng cùng từ vựng "vừa làm vừa học" nhưng chỉ đưa quy tắc *"không vượt quá 150% hệ chính quy"* chứ không có con số. Q5 không nêu bậc học, trong khi corpus có mức đại học (1.910.000đ) và sau đại học (2.865.000đ) — cùng đơn vị đồng/tháng, khác đáp án.

Mỗi câu còn khai báo thêm một trường `must_contain` — chuỗi đặc trưng **phải xuất hiện trong ngữ cảnh truy xuất được** — để chấm được ở mức nội dung chứ không chỉ mức `doc_id`. Khai báo trong `bench.py`, hằng `BENCHMARK_QUERIES`.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Mức thu một tín chỉ | `HeadingChunker` / `RecursiveChunker` / `SentenceChunker` — 2/2 | ✓ cả 4 chiến lược | **`FixedSizeChunker` trượt ở mức nội dung**: gold ở hạng 1 nhưng chuỗi `530.000đ/tín chỉ` rơi vào chỗ nối giữa hai chunk dù đã có overlap 100 |
| 2 | Học phí VLVH *(cần filter)* | `SentenceChunker` — 2/2 | ✓ `SentenceChunker` (hạng 1), `HeadingChunker` (hạng 2) | `FixedSizeChunker` và `RecursiveChunker` **không có gold trong top-3** kể cả khi đã lọc — tài liệu UTT/HVTC chiếm hết slot. Câu hỏi không nêu tên trường nên bản thân nó mơ hồ |
| 3 | Mốc nộp học phí học lại | `FixedSizeChunker` / `HeadingChunker` — 2/2 | ✓ cả 4 lấy đúng tài liệu | **`RecursiveChunker` và `SentenceChunker` cùng 0/2 ở mức nội dung**: đúng tài liệu, sai chunk — mốc ngày bị tách khỏi ngữ cảnh |
| 4 | Lớp học lại ít sinh viên | `FixedSizeChunker` / `HeadingChunker` / `RecursiveChunker` — 2/2 | ✓ cả 4 | **`SentenceChunker` 0/2**: hai vế của điều kiện nằm ở hai chunk khác nhau |
| 5 | Mức thu một tháng *(cần filter)* | Cả 4 chiến lược — 2/2 | ✓ cả 4 | Câu duy nhất **mọi chiến lược đều đạt tối đa** — nhờ filter `level` gom trọn top-3 về đúng tài liệu |

Tổng theo hai cách chấm: `SentenceChunker` 10/10 mức doc_id nhưng 6/10 mức nội dung (chênh **−4**); `FixedSizeChunker` và `RecursiveChunker` 8/10 → 6/10 (chênh −2); `HeadingChunker` 9/10 → 9/10 (**chênh 0**). Chấm theo `doc_id` thổi phồng tới 4 điểm trên 10.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Có, và đo được rõ ràng.** Chạy A/B hai câu cần lọc trên cả 4 chiến lược (8 lượt): filter **cải thiện điểm ở 3 lượt** và **thay đổi thành phần top-3 ở 7/8 lượt**.
> Ca thuyết phục nhất là **Q2 với `HeadingChunker`: không lọc thì top-3 là `ntu · ntu · ntu` — cả ba slot bị bài về Nghị định 238 (`audience=all`) chiếm.** Bài đó nói đúng chủ đề "vừa làm vừa học" nên điểm cosine cao nhất (0.804), nhưng chỉ đưa quy tắc "không vượt quá 150%" chứ không có con số — với sinh viên đang hỏi phải đóng bao nhiêu thì đó là câu trả lời **đúng chủ đề, sai loại thông tin**. Lọc `audience=student` đẩy cả ba ra và đưa tài liệu gold lên hạng 2. Ca này cũng chứng minh vì sao **phải lọc trước rồi mới search**: lọc sau thì còn 0 kết quả dù store vẫn đầy tài liệu hợp lệ.
> Ở Q5, `level=postgraduate` nâng `RecursiveChunker` và `SentenceChunker` từ 1 lên 2 điểm — cả hai vốn để lọt tài liệu bậc đại học (1.910.000đ/tháng) vào top-3, tức **suýt trả lời đúng con số của sai bậc học**. Kết quả này xác nhận nhận định của Hằng theo hướng mạnh hơn: với embedder thật, filter không chỉ tăng precision mà **loại hẳn một loại câu trả lời sai**.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

Công cụ demo: bảng đo tương tác tại **https://claude.ai/artifact/9iEQ63DojtusQYVTg9tsav** (mã nguồn `demo/template.html` + `demo/build.py`; dựng lại bằng `python bench.py --all --json demo/benchmark.json` rồi `python demo/build.py`). Dữ liệu nhúng thẳng vào HTML nên trang chạy offline, không gọi API trong lúc trình bày.

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - **Hai cách chấm cho hai người thắng khác nhau.** `SentenceChunker` thắng 10/10 theo `doc_id` nhưng chỉ 6/10 ở mức nội dung; `HeadingChunker` 9/10 và 9/10. Chênh −4 điểm là phần "top-3 đúng tài liệu nhưng không chunk nào chứa câu trả lời".
> - **Làm sạch dữ liệu quan trọng ngang chọn chunker** *(phát hiện của Thu Hằng).* Menu, nav bar, "Tin liên quan" và footer đều được index thành chunk bình thường; chúng ngắn, lặp lại trên mọi trang, và không có gì đánh dấu chúng là rác — vector store không có cách nào biết. Hằng ghi nhận precision rơi từ 5/5 xuống 2/5 khi chunk trên bản thô, và một câu của bộ query riêng *"lấy nhầm footer website"*. Nhóm xử lý bằng cách làm sạch thủ công và loại hẳn hai trang không có nội dung thật. *(Lưu ý: con số 4/10 của Hằng trên corpus thô và 6/10 của `FixedSizeChunker` trên corpus sạch **không** là một phép A/B — hai lần đo khác nhau cả embedder lẫn bộ câu hỏi. Muốn kết luận chắc, cần chạy lại corpus thô với cùng điều kiện của bảng mục 2.)*
> - **Metadata filter cứu được ca mà cosine chắc chắn sai.** Ở Q2, `HeadingChunker` không lọc thì cả ba slot top-3 là bài Nghị định 238 — điểm cosine cao nhất nhưng không có con số nào.
> - **Embedding không phân biệt được con số.** Hai câu "Học phí thạc sĩ nhân **hệ số 1,5**" và "Học phí tiến sĩ nhân **hệ số 2,5**" có cosine **0.8589**. Với corpus mà đáp án *là* một con số, đây là chế độ hỏng nguy hiểm nhất và nó biện minh cho toàn bộ cách chấm của nhóm.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng corpus, cùng query, cùng code store — bốn chiến lược cho 39 đến 54 chunk, độ dài TB từ 345 đến 556 ký tự, và khác biệt đó quyết định **thông tin nào có cơ hội lọt top-3**. Nhưng bài học lớn hơn: chỉ số dễ đo nhất (`doc_id` có trong top-3 không) lại là chỉ số **sai lệch nhất**. Cả bốn chiến lược đều "tìm đúng tài liệu" gần như mọi lúc — 8 đến 10 trên 10. Khác biệt thật nằm ở chỗ **chunk có tự chứa câu trả lời hay không**, và chỉ số đó đòi hỏi phải khai báo trước từng chuỗi đáp án rồi đi kiểm.
> Một bài học nữa đến từ chính quá trình ghép báo cáo: **ba người đo trên ba điều kiện khác nhau thì ba con số không nói lên điều gì.** Hằng 4/10, Bảo 10/10, Tùng 9/10 — nhìn thì Bảo thắng, nhưng ba con số đó đến từ corpus khác nhau, bộ query khác nhau và ít nhất hai embedder khác nhau. Phải dựng lại bảng đối chứng thì thứ hạng mới hiện ra. Đây chính là lý do lab bắt cả nhóm dùng chung corpus và chung 5 câu hỏi.
> Về phân tích lỗi, nhóm ghi nhận ba failure case thật. **(1)** `SentenceChunker` ở Q4: đáp án bị xé qua hai chunk, gold ở hạng 1 mà vẫn 0 điểm — sửa bằng cách tăng `max_sentences_per_chunk` lên 5–6, thêm overlap một câu, hoặc gom các chunk liền kề cùng `doc_id` trước khi dựng prompt (`chunk_index` đã có sẵn trong metadata). **(2)** `FixedSizeChunker` ở Q1: overlap 100 vẫn không đủ vì USSH lặp lại cùng một con số ở nhiều mục, các chunk "nói về 530.000đ" điểm gần bằng nhau và chunk thật sự chứa chuỗi đó thua sít sao — sửa bằng overlap 20–25% `chunk_size`. **(3)** Q2 mơ hồ về nguồn: câu hỏi không nêu tên trường trong khi corpus gom từ 4 trường, nên không có đáp án duy nhất đúng — sửa bằng cách nêu tên trường hoặc thêm `metadata_filter={"university": ...}`, trường đó đã có trong metadata mà benchmark chưa dùng tới.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> **Chốt corpus và bộ query TRƯỚC khi ai bắt đầu đo** — sai lầm lớn nhất lần này: mỗi người tự crawl, tự làm sạch (hoặc không), tự viết 5 câu hỏi, kết quả là bốn bộ số liệu không ghép được. **Làm sạch ngay sau crawl và loại hẳn trang không có nội dung thật**, thay vì chunk trên bản thô rồi phát hiện footer chiếm top-k. **Đi từ chunk ra câu hỏi, không phải từ câu hỏi ra chunk** — câu hỏi tốt cho benchmark là câu mà một chunk trọn vẹn trả lời được; các câu dạng "áp dụng cho năm học nào" có đáp án nằm ngay trong tiêu đề nên không phân biệt được chiến lược nào tốt hơn. Cuối cùng, **bật embedder thật từ đầu buổi** — nhóm mất nhiều vòng đo vì `MockEmbedder` băm MD5 không có ngữ nghĩa.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **35 / 40** |

Tự trừ ở *Lựa chọn tài liệu*: corpus chỉ đạt 5 tài liệu (mức tối thiểu) vì 3/7 nguồn không dùng được, và hai tài liệu còn thiếu bảng số liệu gốc. Tự trừ ở *Thiết kế chiến lược*: cấu hình `chunk_size=1400` của Bảo chưa được đo trên bảng đối chứng, và Thạch chưa có số liệu tự chạy. Tự trừ ở *Chất lượng truy xuất*: Q2 chỉ đạt 1/2 với chiến lược tốt nhất do câu hỏi không nêu tên trường.

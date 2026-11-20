# Phân tích thực nghiệm thuật toán Mergesort với ngưỡng chuyển đổi `CUTOFF`

## Thông tin sinh viên
* **Họ và tên:** `Vương Thúy Hằng`
* **Mã sinh viên:** `25020144`
* **Học phần:** DSA

---

## 1. Giới thiệu bài toán
Trong cài đặt đệ quy chuẩn của thuật toán **Mergesort**, việc chia nhỏ mảng liên tục xuống tận các mảng con kích thước $1$ phát sinh chi phí phụ trợ (*overhead*) đáng kể do số lượng lời gọi hàm đệ quy lớn và thao tác sao chép mảng phụ `aux[]` lặp đi lặp lại. Để khắc phục, giáo trình đề xuất kỹ thuật lai ghép: chuyển sang dùng **Insertion sort** khi kích thước mảng con nhỏ hơn hoặc bằng một ngưỡng `CUTOFF` (`hi <= lo + CUTOFF - 1`)

Dự án này thực hiện:
1. Cài đặt thuật toán `MergeCutoff` bằng Java bám sát nội dung bài giảng dsa (bảo toàn tính ổn định *stability* và tích hợp cơ chế dừng sớm khi hai nửa mảng đã có thứ tự).
2. Thiết kế quy trình đo đạc thực nghiệm chuẩn hóa trên 5 phân phối dữ liệu (`random`, `sorted`, `reverse`, `partially_sorted`, `duplicates`), 5 bậc kích thước $N \in \{100\,000 \dots 1\,600\,000\}$ và 14 mốc `CUTOFF` từ `1` đến `30`.
3. Xác định giá trị `CUTOFF` tối ưu cho cấu hình máy thực nghiệm qua 5 phiên chạy độc lập (tổng cộng $35\,000$ lượt sắp xếp) và kiểm chứng độ phức tạp tiệm cận $\Theta(N \lg N)$ thông qua Giả thuyết gấp đôi (*Doubling Hypothesis*).

---

## 2. Cấu trúc thư mục dự án

```text
dsa_cutoff/
├── ai-logs/
│   └── log_chat.pdf            # Nhật ký trao đổi với AI trong quá trình làm bài
├── data/
│   ├── README.md               # Mô tả quy tắc sinh và định dạng dữ liệu
│   ├── sample/                 # Bộ dữ liệu mẫu kích thước nhỏ
│   └── generated/              # Dữ liệu thực nghiệm đầy đủ (sinh ra khi chạy DataGenerator)
├── report/
│   ├── Bao_cao_thi_nghiem_Mergesort_CUTOFF.docx  # Báo cáo chi tiết thực nghiệm
├── results/
│   ├── history/                # Kết quả chi tiết của 5 phiên đo (run_1.csv -> run_5.csv)
│   ├── plots/                  # Biểu đồ phân tích hiệu năng và Doubling Hypothesis
│   ├── experiment_runs_table.md / .xlsx  # Bảng tổng hợp thời gian chạy qua các phiên đo
│   ├── raw_results.csv         # Dữ liệu đo của phiên chạy gần nhất
│   ├── summary_stats.csv       # Bảng thống kê tổng hợp theo phân phối và kích thước
│   └── system_info.txt         # Thông số cấu hình phần cứng và JVM của máy đo
├── scripts/
│   ├── track_runs.py           # Lưu lịch sử các phiên đo và xuất bảng tổng hợp (.md, .xlsx)
│   └── analyze_and_plot.py     # Thống kê và vẽ biểu đồ đánh giá hiệu năng & Log-Log
├── src/
│   ├── MergeCutoff.java        # Cài đặt Mergesort cải tiến với tham số CUTOFF
│   ├── DataGenerator.java      # Sinh bộ dữ liệu thực nghiệm cố định (SEED = 42L)
│   └── Benchmark.java          # Chạy đo thời gian thực thi (JVM warm-up, 20 trials)
└── README.md                   # Tài liệu giới thiệu và hướng dẫn chạy dự án
```

---

## 3. Yêu cầu môi trường
* **Java Development Kit (JDK):** Phiên bản 8 trở lên (đã cấu hình biến môi trường `javac` và `java`).
* **Python 3:** Phiên bản 3.8 trở lên.
* **Các thư viện Python sử dụng:** `pandas`, `numpy`, `matplotlib`, `openpyxl`.

---

## 4. Hướng dẫn chạy dự án

Mở Terminal / Command Prompt tại thư mục gốc `dsa_cutoff` và thực hiện tuần tự các bước dưới đây:

### Bước 1: Cài đặt các thư viện Python cần thiết (bỏ qua nếu máy đã cài)
Nếu máy chưa cài đặt các thư viện phân tích và xuất bảng/biểu đồ Python, chạy lệnh sau trước khi thực thi các script:
```bash
pip install pandas numpy matplotlib openpyxl
```
*(Trường hợp Windows báo chưa nhận diện lệnh `pip`, sử dụng lệnh thay thế sau)*:
```bash
python -m pip install pandas numpy matplotlib openpyxl
```
> **Lưu ý xử lý lỗi:** Nếu khi chạy Bước 4 hoặc Bước 5 gặp thông báo `ModuleNotFoundError: No module named '...'` (ví dụ thiếu `openpyxl`, `pandas` hoặc `matplotlib`), chỉ cần chạy lại lệnh cài đặt ở trên để bổ sung thư viện còn thiếu.

### Bước 2: Biên dịch mã nguồn Java
```bash
javac -d bin src/*.java
```

### Bước 3: Sinh bộ dữ liệu thực nghiệm
Chạy lệnh dưới đây **1 lần duy nhất** để tạo toàn bộ các tệp dữ liệu đầu vào trong `data/generated/` (sử dụng `SEED = 42L` để đảm bảo tính tái lập; dữ liệu gốc không bị thay đổi trong suốt quá trình đo):
```bash
java -cp bin DataGenerator
```

### Bước 4: Chạy đo hiệu năng và tổng hợp bảng kết quả
Chạy chương trình `Benchmark` và cập nhật bảng tổng hợp qua `track_runs.py` (có thể chạy lặp lại 3–5 lần để kiểm chứng độ ổn định của kết quả):
```bash
java -cp bin Benchmark
python scripts/track_runs.py
```
Kết quả lưu trữ từng phiên đo được ghi vào `results/history/run_X.csv`, đồng thời xuất bảng tổng hợp đã đánh dấu mốc `CUTOFF` tối ưu tại `results/experiment_runs_table.md` và `results/experiment_runs_table.xlsx`.

### Bước 5: Xuất thống kê và vẽ biểu đồ trực quan
```bash
python scripts/analyze_and_plot.py
```
Các biểu đồ phân tích sẽ được xuất ra thư mục `results/plots/`:
* `1_cutoff_vs_runtime_maxN.png`: So sánh thời gian chạy theo các giá trị `CUTOFF` trên 5 phân phối dữ liệu tại $N = 1\,600\,000$.
* `3_doubling_scaling_loglog.png`: Kiểm chứng Giả thuyết gấp đôi (*Doubling Hypothesis*) trên thang $\log_2 - \log_2$.

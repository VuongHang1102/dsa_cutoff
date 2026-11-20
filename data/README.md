# Dữ liệu thực nghiệm (`data/`)

Bộ dữ liệu gồm mảng đối tượng `Integer[]` (`Comparable[]`), được khởi tạo cố định bằng `src/DataGenerator.java` với **`SEED = 42L`** để đảm bảo tính tái lập 100%.

## 1. Cấu trúc thư mục
* `data/sample/`: Bộ dữ liệu mẫu kích thước nhỏ dùng để kiểm thử nhanh (lưu trên GitHub).
* `data/generated/`: Toàn bộ 25 tệp dữ liệu đầy đủ (bị bỏ qua trong `.gitignore` do dung lượng lớn, tự động sinh trên máy khi chạy code).

## 2. Quy cách bộ dữ liệu (25 tệp)
* **5 kích thước mảng ($N$):** `100,000`, `200,000`, `400,000`, `800,000`, `1,600,000`.
* **5 trạng thái dữ liệu đầu vào:**
  1. `random`: Số nguyên 32-bit ngẫu nhiên phân phối đều.
  2. `sorted`: Mảng tăng dần hoàn toàn ($0, 1, \dots, N-1$).
  3. `reverse`: Mảng giảm dần hoàn toàn ($N, N-1, \dots, 1$).
  4. `partially_sorted`: Mảng tăng dần có hoán đổi ngẫu nhiên $5\%$ số cặp phần tử.
  5. `duplicates`: Mảng nhiều khóa trùng lặp (giá trị ngẫu nhiên trong $\{0 \dots 9\}$).
* **Định dạng tệp (`<data_type>_<N>.txt`):** Dòng đầu ghi số phần tử $N$, các dòng sau lần lượt ghi từng giá trị.

## 3. Cách sinh dữ liệu
Tại thư mục gốc `dsa_cutoff`, chạy **1 lần duy nhất**:
```bash
javac -d bin src/DataGenerator.java
java -cp bin DataGenerator
```
*(Dữ liệu gốc luôn được sao chép độc lập khi chạy `Benchmark.java`, không cần chạy lại `DataGenerator` giữa các phiên đo).*
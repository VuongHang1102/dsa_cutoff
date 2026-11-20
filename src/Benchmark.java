import java.io.*;
import java.util.Arrays;

public class Benchmark {

    // Các kích thước mảng (Doubling Hypothesis)
    private static final int[] SIZES = {100_000, 200_000, 400_000, 800_000, 1_600_000};

    // 5 phân phối dữ liệu đầu vào
    private static final String[] DATA_TYPES = {
        "random", "sorted", "reverse", "partially_sorted", "duplicates"
    };

    // Dải giá trị CUTOFF cần khảo sát (1 = Mergesort nguyên bản, 7 & 10 = mốc giáo trình)
    private static final int[] CUTOFFS = {1, 2, 4, 6, 7, 8, 10, 11, 12, 13, 15, 20, 25, 30};

    private static final int WARMUP_RUNS = 10; // Số lần chạy làm nóng JVM
    private static final int TRIALS = 20;      // Số lần lặp lại phép đo để lấy thống kê

    public static void main(String[] args) throws IOException {
        File csvFile = new File("results/raw_results.csv");
        csvFile.getParentFile().mkdirs();

        saveSystemInfo("results/system_info.txt");
        warmUpJVM();

        try (PrintWriter writer = new PrintWriter(new BufferedWriter(new FileWriter(csvFile)))) {
            writer.println("data_type,size,cutoff,trial,time_ms");

            int totalConfigs = SIZES.length * DATA_TYPES.length * CUTOFFS.length;
            int currentConfig = 0;

            for (int n : SIZES) {
                for (String type : DATA_TYPES) {
                    // Đọc dữ liệu từ file đã sinh (nếu chưa có thì tự động sinh)
                    Integer[] originalData = loadOrGenerateData(n, type);

                    for (int cutoff : CUTOFFS) {
                        currentConfig++;
                        System.out.printf("[%d/%d] Dang do: type=%-16s | N=%-8d | CUTOFF=%-2d ... ",
                                currentConfig, totalConfigs, type, n, cutoff);

                        // Gợi ý dọn rác trước mỗi cấu hình mới để giảm nhiễu GC
                        System.gc();

                        double totalMs = 0.0;
                        for (int trial = 1; trial <= TRIALS; trial++) {
                            // Luôn sao chép mảng gốc chưa sắp xếp cho mỗi lần đo
                            Integer[] copy = Arrays.copyOf(originalData, originalData.length);

                            long startTime = System.nanoTime();
                            MergeCutoff.sort(copy, cutoff);
                            long endTime = System.nanoTime();

                            // Kiểm tra tính đúng đắn ở lần chạy đầu tiên (không tính vào thời gian đo)
                            if (trial == 1 && !isSorted(copy)) {
                                throw new IllegalStateException("Loi: Mang chua duoc sap xep dung!");
                            }

                            double elapsedMs = (endTime - startTime) / 1_000_000.0;
                            totalMs += elapsedMs;

                            writer.printf("%s,%d,%d,%d,%.6f%n", type, n, cutoff, trial, elapsedMs);
                        }
                        writer.flush();
                        System.out.printf("Mean = %.3f ms%n", totalMs / TRIALS);
                    }
                }
            }
        }
        System.out.println("\nHoan tat thuc nghiem! Ket qua da luu tai: results/raw_results.csv");
    }

    /**
     * Chạy nháp thuật toán để kích hoạt trình biên dịch JIT của JVM.
     */
    private static void warmUpJVM() {
        System.out.println("Dang chay JVM warm-up...");
        Integer[] warmupBase = DataGenerator.generate(100_000, "random");
        for (int i = 0; i < WARMUP_RUNS; i++) {
            for (int cutoff : new int[]{1, 7, 10, 20}) {
                Integer[] copy = Arrays.copyOf(warmupBase, warmupBase.length);
                MergeCutoff.sort(copy, cutoff);
            }
        }
        System.out.println("JVM warm-up hoan tat.\n");
    }

    /**
     * Đọc dữ liệu từ thư mục data/sample hoặc data/generated.
     * Nếu chưa tồn tại file, tự động gọi DataGenerator để tạo mảng.
     */
    private static Integer[] loadOrGenerateData(int n, String type) throws IOException {
        String folder = (n <= 100_000) ? "data/sample" : "data/generated";
        File file = new File(folder + "/" + type + "_" + n + ".txt");

        if (!file.exists()) {
            return DataGenerator.generate(n, type);
        }

        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            int size = Integer.parseInt(reader.readLine().trim());
            Integer[] data = new Integer[size];
            for (int i = 0; i < size; i++) {
                data[i] = Integer.parseInt(reader.readLine().trim());
            }
            return data;
        }
    }

    /**
     * Kiểm tra mảng đã được sắp xếp tăng dần hay chưa.
     */
    private static boolean isSorted(Comparable[] a) {
        for (int i = 1; i < a.length; i++) {
            if (a[i].compareTo(a[i - 1]) < 0) return false;
        }
        return true;
    }

    /**
     * Xuất thông tin phần cứng và môi trường Java phục vụ báo cáo.
     */
    private static void saveSystemInfo(String filePath) throws IOException {
        try (PrintWriter out = new PrintWriter(new FileWriter(filePath))) {
            out.println("=== CAU HINH HE THONG THUC NGHIEM ===");
            out.println("OS Name        : " + System.getProperty("os.name"));
            out.println("OS Version     : " + System.getProperty("os.version"));
            out.println("Architecture   : " + System.getProperty("os.arch"));
            out.println("Java Version   : " + System.getProperty("java.version"));
            out.println("JVM Name       : " + System.getProperty("java.vm.name"));
            out.println("CPU Cores      : " + Runtime.getRuntime().availableProcessors());
            out.printf("Max JVM Heap   : %.2f MB%n", Runtime.getRuntime().maxMemory() / (1024.0 * 1024.0));
        }
    }
}
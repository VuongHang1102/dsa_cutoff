import java.io.*;
import java.util.Random;

public class DataGenerator {
    private static final long SEED = 42L;

    public static Integer[] generate(int n, String type) {
        Random rand = new Random(SEED);
        Integer[] a = new Integer[n];

        switch (type) {
            case "random":
                for (int i = 0; i < n; i++) a[i] = rand.nextInt();
                break;
            case "sorted":
                for (int i = 0; i < n; i++) a[i] = i;
                break;
            case "reverse":
                for (int i = 0; i < n; i++) a[i] = n - i;
                break;
            case "partially_sorted":
                for (int i = 0; i < n; i++) a[i] = i;
                int swaps = (int) (n * 0.05); // Hoán đổi ngẫu nhiên 5% số phần tử
                for (int s = 0; s < swaps; s++) {
                    int idx1 = rand.nextInt(n);
                    int idx2 = rand.nextInt(n);
                    Integer tmp = a[idx1]; a[idx1] = a[idx2]; a[idx2] = tmp;
                }
                break;
            case "duplicates":
                for (int i = 0; i < n; i++) a[i] = rand.nextInt(10); // Chỉ 10 giá trị phân biệt
                break;
            default:
                throw new IllegalArgumentException("Unknown data type: " + type);
        }
        return a;
    }

    public static void saveToFile(Integer[] a, String filePath) throws IOException {
        File file = new File(filePath);
        file.getParentFile().mkdirs();
        try (PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter(file)))) {
            out.println(a.length);
            for (Integer val : a) out.println(val);
        }
    }

    public static void main(String[] args) throws IOException {
        int[] sizes = {100_000, 200_000, 400_000, 800_000, 1_600_000};
        String[] types = {"random", "sorted", "reverse", "partially_sorted", "duplicates"};

        for (int n : sizes) {
            for (String type : types) {
                Integer[] data = generate(n, type);
                String folder = (n <= 100_000) ? "data/sample" : "data/generated";
                saveToFile(data, folder + "/" + type + "_" + n + ".txt");
            }
        }
        System.out.println("Da sinh xong bo du lieu thuc nghiem.");
    }
}
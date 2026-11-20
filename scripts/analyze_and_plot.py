import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Cấu hình font và giao diện biểu đồ
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]
plt.rcParams["axes.unicode_minus"] = False
plt.style.use("seaborn-v0_8-whitegrid")

HISTORY_DIR = "results/history"
RAW_CSV = "results/raw_results.csv"
SUMMARY_CSV = "results/summary_stats.csv"
PLOT_DIR = "results/plots"


def load_all_runs() -> pd.DataFrame:
    """Đọc toàn bộ các file run_*.csv trong results/history (hoặc fallback về raw_results.csv)."""
    run_files = sorted(
        glob.glob(os.path.join(HISTORY_DIR, "run_*.csv")),
        key=lambda p: int(os.path.basename(p).split("_")[1].split(".")[0]),
    )

    if run_files:
        dfs = []
        for idx, fpath in enumerate(run_files, start=1):
            df = pd.read_csv(fpath)
            df["run"] = idx
            dfs.append(df)
        print(f"Đã tải dữ liệu tổng hợp từ {len(run_files)} lần chạy trong '{HISTORY_DIR}/'.")
        return pd.concat(dfs, ignore_index=True)

    if os.path.exists(RAW_CSV):
        df = pd.read_csv(RAW_CSV)
        df["run"] = 1
        print(f"Không thấy thư mục history, đang dùng dữ liệu từ '{RAW_CSV}'.")
        return df

    raise FileNotFoundError("Không tìm thấy dữ liệu thực nghiệm nào để phân tích!")


def compute_statistics(full_df: pd.DataFrame) -> pd.DataFrame:
    """Tính thống kê tổng hợp trên toàn bộ các lần chạy."""
    # Trước tiên tính trung bình của từng lần chạy (run)
    per_run = (
        full_df.groupby(["run", "data_type", "size", "cutoff"])["time_ms"]
        .mean()
        .reset_index()
    )

    # Sau đó lấy trung bình cộng qua các lần chạy (mean of runs)
    stats = (
        per_run.groupby(["data_type", "size", "cutoff"])["time_ms"]
        .agg(
            num_runs="count",
            mean_ms="mean",
            std_between_runs_ms="std",
            min_run_ms="min",
            max_run_ms="max",
        )
        .reset_index()
    )
    return stats


def print_optimal_summary(stats: pd.DataFrame):
    """In bảng tổng kết nội bộ giữa các giá trị CUTOFF đã chạy trên máy."""
    print("\n" + "=" * 92)
    print(
        f"{'DATA TYPE':<18} | {'SIZE (N)':<10} | {'BEST C':<6} | {'BEST (ms)':<10} | "
        f"{'WORST C':<7} | {'WORST (ms)':<10} | {'GIẢM TỐI ĐA':<11}"
    )
    print("=" * 92)

    for (dtype, size), group in stats.groupby(["data_type", "size"]):
        best_row = group.loc[group["mean_ms"].idxmin()]
        worst_row = group.loc[group["mean_ms"].idxmax()]
        reduction_pct = (
            (worst_row["mean_ms"] - best_row["mean_ms"]) / worst_row["mean_ms"] * 100.0
        )

        print(
            f"{dtype:<18} | {size:<10,d} | {int(best_row['cutoff']):<6d} | "
            f"{best_row['mean_ms']:<10.3f} | {int(worst_row['cutoff']):<7d} | "
            f"{worst_row['mean_ms']:<10.3f} | {reduction_pct:>9.2f}%"
        )
    print("=" * 92 + "\n")


def plot_cutoff_by_datatype(full_df: pd.DataFrame, stats: pd.DataFrame):
    """Đồ thị 1: Vẽ 5 đường (cùng màu) cho 5 lần đo và 1 đường màu đỏ là trung bình cộng."""
    max_n = full_df["size"].max()
    sub_all = full_df[full_df["size"] == max_n]
    sub_stats = stats[stats["size"] == max_n]

    runs = sorted(sub_all["run"].unique())
    tested_cutoffs = sorted(sub_all["cutoff"].unique())

    # Tính trung bình theo từng lần chạy ở kích thước N lớn nhất
    per_run_mean = (
        sub_all.groupby(["run", "data_type", "cutoff"])["time_ms"]
        .mean()
        .reset_index()
    )

    data_types = ["random", "sorted", "reverse", "partially_sorted", "duplicates"]
    titles = {
        "random": "1. Ngẫu nhiên (Uniform Random)",
        "sorted": "2. Đã sắp xếp tăng dần (Sorted)",
        "reverse": "3. Sắp xếp ngược (Reverse Sorted)",
        "partially_sorted": "4. Gần có thứ tự (Partially Sorted)",
        "duplicates": "5. Nhiều khóa trùng lặp (Duplicates)",
    }

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.flatten()

    for idx, dtype in enumerate(data_types):
        ax = axes[idx]

        # 1. Vẽ các đường từng lần chạy với CÙNG MỘT MÀU
        for r_idx, r in enumerate(runs):
            d_run = per_run_mean[
                (per_run_mean["data_type"] == dtype) & (per_run_mean["run"] == r)
            ].sort_values("cutoff")

            ax.plot(
                d_run["cutoff"],
                d_run["time_ms"],
                color="#5b9bd5",
                alpha=0.55,
                linewidth=1.4,
                marker="o",
                markersize=3.5,
                label=f"Từng lần đo ({len(runs)} lần)" if r_idx == 0 else None,
            )

        # 2. Vẽ đường MÀU ĐỎ biểu thị trung bình cộng của tất cả các lần đo
        d_avg = sub_stats[sub_stats["data_type"] == dtype].sort_values("cutoff")
        best_row = d_avg.loc[d_avg["mean_ms"].idxmin()]

        ax.plot(
            d_avg["cutoff"],
            d_avg["mean_ms"],
            color="#d62728",
            linewidth=2.4,
            marker="o",
            markersize=5,
            zorder=4,
            label="Trung bình cộng các lần đo",
        )

        # Đánh dấu điểm tối ưu trên đường trung bình đỏ
        ax.scatter(
            [best_row["cutoff"]],
            [best_row["mean_ms"]],
            color="#990000",
            s=140,
            zorder=5,
            marker="*",
            label=f"Tối ưu TB (C = {int(best_row['cutoff'])})",
        )

        if len(tested_cutoffs) <= 15:
            ax.set_xticks(tested_cutoffs)

        ax.set_title(titles[dtype], fontsize=11, fontweight="bold")
        ax.set_xlabel("Giá trị CUTOFF đã đo", fontsize=10)
        ax.set_ylabel("Thời gian chạy (ms)", fontsize=10)
        ax.legend(fontsize=8.5, loc="best")

    # Ô trống thứ 6 dùng làm thông tin cấu hình đo
    axes[5].axis("off")
    summary_text = (
        f"THÔNG SỐ THỰC NGHIỆM TỔNG HỢP\n"
        f"• Kích thước mảng: N = {max_n:,}\n"
        f"• Số phiên chạy độc lập: {len(runs)} lần\n"
        f"• Dải CUTOFF đo: {tested_cutoffs[0]} → {tested_cutoffs[-1]} ({len(tested_cutoffs)} mốc)\n"
        f"• Đường xanh nhạt: Kết quả từng lần chạy\n"
        f"• Đường đỏ đậm: Trung bình cộng {len(runs)} lần đo\n"
        f"• Sao đỏ (*): CUTOFF đạt thời gian TB nhỏ nhất"
    )
    axes[5].text(
        0.05,
        0.5,
        summary_text,
        fontsize=10.5,
        va="center",
        bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8f9fa", edgecolor="#cccccc"),
    )

    fig.suptitle(
        f"So sánh thời gian chạy giữa các giá trị CUTOFF qua {len(runs)} lần đo (N = {max_n:,})",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = os.path.join(PLOT_DIR, "1_cutoff_vs_runtime_maxN.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Đã lưu biểu đồ 1: {out_path}")


def plot_doubling_hypothesis(stats: pd.DataFrame):
    """Đồ thị 3: Kiểm chứng Doubling Hypothesis trên thang Log-Log (dữ liệu Random tổng hợp)."""
    sub = stats[stats["data_type"] == "random"].copy()
    available_cutoffs = sorted(sub["cutoff"].unique())
    max_n = sub["size"].max()
    best_c = int(sub[sub["size"] == max_n].sort_values("mean_ms").iloc[0]["cutoff"])

    if len(available_cutoffs) <= 6:
        compare_cutoffs = available_cutoffs
    else:
        mid_c = available_cutoffs[len(available_cutoffs) // 2]
        compare_cutoffs = sorted(
            list({available_cutoffs[0], mid_c, best_c, available_cutoffs[-1]})
        )

    plt.figure(figsize=(10, 6))
    for c in compare_cutoffs:
        d = sub[sub["cutoff"] == c].sort_values("size")
        ratios = d["mean_ms"].values[1:] / d["mean_ms"].values[:-1]
        avg_ratio = np.mean(ratios)

        tag = " (Tối ưu)" if c == best_c else ""
        plt.loglog(
            d["size"],
            d["mean_ms"],
            marker="s",
            linewidth=2.2,
            base=2,
            label=f"CUTOFF = {c}{tag} — Doubling Ratio ≈ {avg_ratio:.2f}",
        )

    plt.title(
        "Kiểm chứng Giả thuyết gấp đôi (Log-Log Plot) trên dữ liệu Ngẫu nhiên",
        fontsize=13,
        fontweight="bold",
    )
    plt.xlabel("Kích thước mảng N (thang log2)", fontsize=11)
    plt.ylabel("Thời gian chạy trung bình (ms - thang log2)", fontsize=11)
    plt.legend(fontsize=10)
    plt.tight_layout()

    out_path = os.path.join(PLOT_DIR, "3_doubling_scaling_loglog.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Đã lưu biểu đồ 3: {out_path}")


def main():
    os.makedirs(PLOT_DIR, exist_ok=True)
    full_df = load_all_runs()

    stats = compute_statistics(full_df)
    stats.to_csv(SUMMARY_CSV, index=False)
    print(f"Đã xuất bảng thống kê chi tiết tại: {SUMMARY_CSV}")

    print_optimal_summary(stats)
    plot_cutoff_by_datatype(full_df, stats)
    plot_doubling_hypothesis(stats)


if __name__ == "__main__":
    main()
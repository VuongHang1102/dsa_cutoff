import os
import glob
import shutil
import hashlib
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

RAW_CSV = "results/raw_results.csv"
HISTORY_DIR = "results/history"
OUT_MD = "results/experiment_runs_table.md"
OUT_XLSX = "results/experiment_runs_table.xlsx"


def file_md5(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def archive_current_run() -> list[str]:
    """Lưu raw_results.csv thành run_X.csv mới nếu chưa tồn tại bản trùng lặp."""
    if not os.path.exists(RAW_CSV):
        raise FileNotFoundError(f"Không tìm thấy {RAW_CSV}. Hãy chạy Benchmark.java trước!")

    os.makedirs(HISTORY_DIR, exist_ok=True)
    existing_files = sorted(
        glob.glob(os.path.join(HISTORY_DIR, "run_*.csv")),
        key=lambda p: int(os.path.basename(p).split("_")[1].split(".")[0]),
    )

    current_hash = file_md5(RAW_CSV)
    is_duplicate = any(file_md5(p) == current_hash for p in existing_files)

    if not is_duplicate:
        next_idx = len(existing_files) + 1
        dest_path = os.path.join(HISTORY_DIR, f"run_{next_idx}.csv")
        shutil.copy2(RAW_CSV, dest_path)
        existing_files.append(dest_path)
        print(f"Đã lưu kết quả lần chạy mới vào: {dest_path}")
    else:
        print("Dữ liệu raw_results.csv hiện tại đã được lưu trước đó, tiến hành tổng hợp lại bảng.")

    return existing_files


def build_summary_tables(run_files: list[str]):
    """Tính thời gian trung bình và xác định CUTOFF tối ưu cho từng lần chạy."""
    all_runs = []
    for idx, fpath in enumerate(run_files, start=1):
        df = pd.read_csv(fpath)
        df["run"] = idx
        all_runs.append(df)

    full_df = pd.concat(all_runs, ignore_index=True)
    cutoffs = sorted(full_df["cutoff"].unique())

    # Bảng 1: Thời gian trung bình (ms) trên tất cả các trường hợp theo từng lần chạy
    pivot_mean = (
        full_df.groupby(["run", "cutoff"])["time_ms"]
        .mean()
        .unstack("cutoff")
        .reindex(columns=cutoffs)
    )

    # Tìm CUTOFF có thời gian trung bình nhỏ nhất cho từng lần chạy
    best_cutoff_per_run = pivot_mean.idxmin(axis=1)

    # Tính dòng Trung bình qua tất cả các lần chạy
    overall_mean_row = pivot_mean.mean(axis=0)
    overall_best_cutoff = overall_mean_row.idxmin()
    avg_of_best_cutoffs = best_cutoff_per_run.mean()

    # Bảng 2: CUTOFF tối ưu theo từng loại dữ liệu ở kích thước N lớn nhất
    max_n = full_df["size"].max()
    sub_max_n = full_df[full_df["size"] == max_n]
    data_types = ["random", "sorted", "reverse", "partially_sorted", "duplicates"]
    available_types = [t for t in data_types if t in sub_max_n["data_type"].unique()]

    dtype_mean = (
        sub_max_n.groupby(["run", "data_type", "cutoff"])["time_ms"]
        .mean()
        .reset_index()
    )
    best_by_dtype = (
        dtype_mean.loc[dtype_mean.groupby(["run", "data_type"])["time_ms"].idxmin()]
        .pivot(index="run", columns="data_type", values="cutoff")
        .reindex(columns=available_types)
    )
    best_by_dtype["TB_CUTOFF_toi_uu"] = best_by_dtype.mean(axis=1)

    return (
        cutoffs,
        pivot_mean,
        best_cutoff_per_run,
        overall_mean_row,
        overall_best_cutoff,
        avg_of_best_cutoffs,
        max_n,
        best_by_dtype,
    )


def export_markdown(
    cutoffs,
    pivot_mean,
    best_cutoff_per_run,
    overall_mean_row,
    overall_best_cutoff,
    avg_of_best_cutoffs,
    max_n,
    best_by_dtype,
):
    """Xuất bảng Markdown với định dạng bôi đen (**...**) cho giá trị tối ưu."""
    lines = []
    lines.append("# Tổng hợp kết quả thực nghiệm qua nhiều lần chạy\n")
    lines.append("## 1. Thời gian chạy trung bình (ms) trên tất cả các trường hợp\n")

    header = ["Lần chạy"] + [f"C = {c}" for c in cutoffs] + ["CUTOFF tối ưu (TB tất cả TH)"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join([":---"] + [":---:"] * (len(header) - 1)) + " |")

    for run_idx, row in pivot_mean.iterrows():
        best_c = best_cutoff_per_run.loc[run_idx]
        cells = [f"**Lần {run_idx}**"]
        for c in cutoffs:
            val_str = f"{row[c]:.3f}"
            cells.append(f"**{val_str}**" if c == best_c else val_str)
        cells.append(f"**`{int(best_c)}`**")
        lines.append("| " + " | ".join(cells) + " |")

    # Dòng tổng hợp trung bình tất cả các lần chạy
    avg_cells = ["**Trung bình các lần**"]
    for c in cutoffs:
        val_str = f"{overall_mean_row[c]:.3f}"
        avg_cells.append(f"**{val_str}**" if c == overall_best_cutoff else val_str)
    avg_cells.append(f"**`{int(overall_best_cutoff)}` (TB: `{avg_of_best_cutoffs:.2f}`)**")
    lines.append("| " + " | ".join(avg_cells) + " |\n")

    # Bảng 2: Chi tiết theo từng loại dữ liệu
    lines.append(f"## 2. Giá trị CUTOFF tối ưu theo từng phân phối dữ liệu (N = {max_n:,})\n")
    dtypes = [c for c in best_by_dtype.columns if c != "TB_CUTOFF_toi_uu"]
    header2 = ["Lần chạy"] + dtypes + ["CUTOFF tối ưu trung bình"]
    lines.append("| " + " | ".join(header2) + " |")
    lines.append("| " + " | ".join([":---"] + [":---:"] * (len(header2) - 1)) + " |")

    for run_idx, row in best_by_dtype.iterrows():
        cells = [f"**Lần {run_idx}**"]
        for dt in dtypes:
            cells.append(f"{int(row[dt])}")
        cells.append(f"**`{row['TB_CUTOFF_toi_uu']:.2f}`**")
        lines.append("| " + " | ".join(cells) + " |")

    avg_dt_cells = ["**Trung bình các lần**"]
    for dt in dtypes:
        avg_dt_cells.append(f"**{best_by_dtype[dt].mean():.2f}**")
    avg_dt_cells.append(f"**`{best_by_dtype['TB_CUTOFF_toi_uu'].mean():.2f}`**")
    lines.append("| " + " | ".join(avg_dt_cells) + " |\n")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Đã xuất bảng Markdown (đã bôi đen giá trị tối ưu) tại: {OUT_MD}")


def export_excel(
    cutoffs,
    pivot_mean,
    best_cutoff_per_run,
    overall_mean_row,
    overall_best_cutoff,
    avg_of_best_cutoffs,
):
    """Xuất file Excel tự động bôi đen (in đậm + tô nền) giá trị tối ưu sau mỗi lần chạy."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Tong_hop_CUTOFF"

    header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    highlight_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    bold_font = Font(bold=True, color="000000")
    normal_font = Font(bold=False, color="000000")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="BFBFBF"),
        right=Side(style="thin", color="BFBFBF"),
        top=Side(style="thin", color="BFBFBF"),
        bottom=Side(style="thin", color="BFBFBF"),
    )

    headers = ["Lần chạy"] + [f"CUTOFF = {c} (ms)" for c in cutoffs] + ["CUTOFF tối ưu (TB tất cả TH)"]
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = thin_border

    # Ghi từng lần chạy
    for r_offset, (run_idx, row) in enumerate(pivot_mean.iterrows(), start=2):
        best_c = best_cutoff_per_run.loc[run_idx]
        ws.cell(row=r_offset, column=1, value=f"Lần {run_idx}").font = bold_font

        for c_offset, c in enumerate(cutoffs, start=2):
            cell = ws.cell(row=r_offset, column=c_offset, value=round(float(row[c]), 3))
            cell.number_format = "0.000"
            if c == best_c:
                cell.font = bold_font
                cell.fill = highlight_fill
            else:
                cell.font = normal_font

        best_cell = ws.cell(row=r_offset, column=len(headers), value=int(best_c))
        best_cell.font = bold_font
        best_cell.fill = highlight_fill

        for col_idx in range(1, len(headers) + 1):
            ws.cell(row=r_offset, column=col_idx).alignment = center_align
            ws.cell(row=r_offset, column=col_idx).border = thin_border

    # Ghi dòng Trung bình tổng hợp ở cuối bảng
    summary_row = len(pivot_mean) + 2
    ws.cell(row=summary_row, column=1, value="Trung bình các lần").font = bold_font
    for c_offset, c in enumerate(cutoffs, start=2):
        cell = ws.cell(row=summary_row, column=c_offset, value=round(float(overall_mean_row[c]), 3))
        cell.number_format = "0.000"
        cell.font = bold_font
        if c == overall_best_cutoff:
            cell.fill = highlight_fill

    final_best_cell = ws.cell(
        row=summary_row,
        column=len(headers),
        value=f"{int(overall_best_cutoff)} (TB: {avg_of_best_cutoffs:.2f})",
    )
    final_best_cell.font = bold_font
    final_best_cell.fill = highlight_fill

    for col_idx in range(1, len(headers) + 1):
        ws.cell(row=summary_row, column=col_idx).alignment = center_align
        ws.cell(row=summary_row, column=col_idx).border = thin_border
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 18

    wb.save(OUT_XLSX)
    print(f"Đã xuất bảng Excel (đã bôi đen giá trị tối ưu) tại: {OUT_XLSX}")


def main():
    run_files = archive_current_run()
    results = build_summary_tables(run_files)
    export_markdown(*results)
    export_excel(*results[:6])


if __name__ == "__main__":
    main()
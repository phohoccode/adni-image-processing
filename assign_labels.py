import os
import shutil
import pandas as pd

# ============ CONFIG ============
DATASET_2D = r"D:\KhoaLuanTotNghiep\code\dataset_2d"
CSV_PATH   = r"D:\KhoaLuanTotNghiep\ADNIMERGE_30Jan2026.csv"
OUT_DIR    = r"D:\KhoaLuanTotNghiep\code\dataset_labeled"
# ================================


def load_label_map(csv_path):
    """
    Load label map từ CSV file.
    
    Args:
        csv_path: Đường dẫn đến CSV chứa thông tin label
    
    Returns:
        dict: {PTID: DX_label}
    """
    df = pd.read_csv(csv_path)
    df = df[["PTID", "DX"]].dropna()
    df = df.drop_duplicates("PTID")
    return dict(zip(df.PTID, df.DX))


def assign_labels_for_subject(subject_dir, subject_name, label, output_dir, log_callback=None):
    """
    Copy các slice PNG của 1 subject vào thư mục label tương ứng.
    
    Args:
        subject_dir: Thư mục chứa các PNG slice của subject
        subject_name: Tên subject (PTID)
        label: Nhãn (DX) của subject
        output_dir: Thư mục output tổng
        log_callback: Function để log (optional)
    
    Returns:
        int: Số slice đã copy
    """
    out_label_dir = os.path.join(output_dir, label)
    os.makedirs(out_label_dir, exist_ok=True)
    
    slice_count = 0
    for fname in os.listdir(subject_dir):
        if not fname.endswith(".png"):
            continue
        
        src = os.path.join(subject_dir, fname)
        dst = os.path.join(out_label_dir, f"{subject_name}_{fname}")  # đảm bảo unique
        shutil.copy2(src, dst)
        slice_count += 1
    
    if log_callback and slice_count > 0:
        log_callback(f"[LABEL] {subject_name} → {label} ({slice_count} slices)")
    
    return slice_count


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    # Load labels
    label_map = load_label_map(CSV_PATH)

    processed = 0
    for subj in os.listdir(DATASET_2D):
        subj_dir = os.path.join(DATASET_2D, subj)
        if not os.path.isdir(subj_dir):
            continue

        if subj not in label_map:
            print(f"[SKIP] Không có label: {subj}")
            continue

        label = label_map[subj]
        slice_count = assign_labels_for_subject(subj_dir, subj, label, OUT_DIR, print)
        
        if slice_count > 0:
            processed += 1
    
    print(f"\nDone. Processed {processed} subjects.")

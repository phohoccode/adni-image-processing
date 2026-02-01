# Import các thư viện cần thiết
import os          # Thao tác với file và thư mục
import shutil      # Copy file
import pandas as pd # Đọc và xử lý file CSV

# ============ CẤU HÌNH ============
# Thư mục chứa dataset 2D đã tạo từ bước trước (các slice PNG)
DATASET_2D = r"D:\KhoaLuanTotNghiep\code\dataset_2d"
# File CSV chứa thông tin nhãn (DX: diagnosis) của các subject
CSV_PATH   = r"D:\KhoaLuanTotNghiep\ADNIMERGE_30Jan2026.csv"
# Thư mục output để lưu dataset đã được gán nhãn (phân theo class)
OUT_DIR    = r"D:\KhoaLuanTotNghiep\code\dataset_labeled"
# ====================================


def load_label_map(csv_path):
    """
    Load label map từ CSV file và tạo dictionary ánh xạ PTID -> DX.
    
    Quy trình:
    1. Đọc CSV file
    2. Lọc chỉ lấy cột PTID và DX
    3. Loại bỏ các dòng có giá trị null
    4. Loại bỏ các PTID trùng lặp (giữ lại dòng đầu tiên)
    5. Tạo dictionary mapping
    
    Args:
        csv_path: Đường dẫn đến CSV chứa thông tin label
    
    Returns:
        dict: {PTID: DX_label} - Dictionary ánh xạ subject ID sang nhãn chẩn đoán
    """
    # Đọc file CSV
    df = pd.read_csv(csv_path)
    # Chỉ lấy 2 cột PTID (Patient ID) và DX (Diagnosis), loại bỏ các dòng có giá trị null
    df = df[["PTID", "DX"]].dropna()
    # Loại bỏ các PTID trùng lặp, chỉ giữ lại lần xuất hiện đầu tiên
    df = df.drop_duplicates("PTID")
    # Tạo dictionary từ 2 cột PTID và DX
    return dict(zip(df.PTID, df.DX))


def assign_labels_for_subject(subject_dir, subject_name, label, output_dir, log_callback=None):
    """
    Copy các slice PNG của 1 subject vào thư mục label tương ứng.
    
    Tổ chức thư mục output theo cấu trúc:
    output_dir/
        ├── CN/          (Cognitive Normal)
        ├── MCI/         (Mild Cognitive Impairment)
        └── Dementia/    (hoặc các label khác)
            ├── 002_S_0295_000.png
            ├── 002_S_0295_001.png
            └── ...
    
    Args:
        subject_dir: Thư mục chứa các PNG slice của subject
        subject_name: Tên subject (PTID)
        label: Nhãn (DX) của subject - ví dụ: "CN", "MCI", "Dementia"
        output_dir: Thư mục output tổng
        log_callback: Function để log (optional)
    
    Returns:
        int: Số slice đã copy
    """
    # Tạo thư mục con cho label này (ví dụ: dataset_labeled/CN/)
    out_label_dir = os.path.join(output_dir, label)
    os.makedirs(out_label_dir, exist_ok=True)
    
    # Đếm số slice đã copy
    slice_count = 0
    # Duyệt qua tất cả file trong thư mục subject
    for fname in os.listdir(subject_dir):
        # Chỉ xử lý file PNG
        if not fname.endswith(".png"):
            continue
        
        # Đường dẫn source (file gốc)
        src = os.path.join(subject_dir, fname)
        # Đường dẫn destination với prefix là subject_name để đảm bảo tên file unique
        # Ví dụ: 002_S_0295_000.png thay vì chỉ 000.png
        dst = os.path.join(out_label_dir, f"{subject_name}_{fname}")
        # Copy file (copy2 giữ nguyên metadata như timestamp)
        shutil.copy2(src, dst)
        slice_count += 1
    
    # Log nếu có callback và đã copy được slice
    if log_callback and slice_count > 0:
        log_callback(f"[LABEL] {subject_name} → {label} ({slice_count} slices)")
    
    return slice_count


# Chương trình chính
if __name__ == "__main__":
    # Tạo thư mục output nếu chưa tồn tại
    os.makedirs(OUT_DIR, exist_ok=True)

    # Load label map từ CSV file (PTID -> DX)
    label_map = load_label_map(CSV_PATH)

    # Đếm số subject đã xử lý thành công
    processed = 0
    
    # Duyệt qua tất cả thư mục subject trong dataset_2d
    for subj in os.listdir(DATASET_2D):
        # Đường dẫn đầy đủ đến thư mục subject
        subj_dir = os.path.join(DATASET_2D, subj)
        # Bỏ qua nếu không phải là thư mục
        if not os.path.isdir(subj_dir):
            continue

        # Kiểm tra xem subject có trong label map không
        if subj not in label_map:
            print(f"[SKIP] Không có label: {subj}")
            continue

        # Lấy label (DX) của subject từ label map
        label = label_map[subj]
        # Copy các slice của subject vào thư mục label tương ứng
        slice_count = assign_labels_for_subject(subj_dir, subj, label, OUT_DIR, print)
        
        # Tăng counter nếu đã copy được ít nhất 1 slice
        if slice_count > 0:
            processed += 1
    
    # In thông báo hoàn thành
    print(f"\nDone. Processed {processed} subjects.")

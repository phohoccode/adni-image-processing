# Import các thư viện cần thiết
import os          # Thao tác với file và thư mục
import numpy as np # Xử lý mảng và tính toán số học
import nibabel as nib  # Đọc file NIfTI (định dạng ảnh não phổ biến)
import cv2         # OpenCV - resize và xử lý ảnh
import imageio     # Lưu ảnh dưới dạng PNG

# ============ CẤU HÌNH ============
# Thư mục chứa các file não đã loại bỏ skull (_brain.nii.gz)
BRAIN_DIR   = r"D:\KhoaLuanTotNghiep\code\skull_stripped"
# Thư mục đầu ra để lưu dataset 2D
OUT_DIR     = r"D:\KhoaLuanTotNghiep\code\dataset_2d"
# Kích thước ảnh output (128x128 pixels)
OUT_SIZE    = 128
# Số slice trích xuất từ mỗi subject (nên là số lẻ để có slice trung tâm)
NUM_SLICES  = 11
# ====================================

def load_and_norm(path):
    """
    Load và chuẩn hóa NIfTI volume về khoảng [0, 1]
    
    Args:
        path: Đường dẫn đến file .nii hoặc .nii.gz
    
    Returns:
        numpy.ndarray: Volume đã được chuẩn hóa về [0, 1]
    """
    # Đọc file NIfTI
    vol = nib.load(path)
    # Chuyển về dạng canonical (chuẩn hóa hướng) và lấy dữ liệu dạng numpy array
    vol = nib.as_closest_canonical(vol).get_fdata()

    # Lấy các voxel não (giá trị > 0, loại bỏ background)
    brain = vol[vol > 0]
    # Tính percentile 2% và 98% để loại bỏ outliers
    p2, p98 = np.percentile(brain, (2, 98))
    # Clip các giá trị về khoảng [p2, p98]
    vol = np.clip(vol, p2, p98)
    # Chuẩn hóa về khoảng [0, 1]
    vol = (vol - p2) / (p98 - p2 + 1e-8)

    return vol

def process_subject_to_2d(brain_file_path, output_dir, out_size=128, num_slices=11, log_callback=None):
    """
    Xử lý 1 subject từ file _brain.nii.gz thành các slice 2D PNG.
    
    Quy trình:
    1. Load và chuẩn hóa volume 3D
    2. Tìm slice có diện tích não lớn nhất (trục Y)
    3. Lấy các slice xung quanh slice trung tâm
    4. Rotate, resize và lưu thành PNG
    
    Args:
        brain_file_path: Đường dẫn đến file _brain.nii.gz
        output_dir: Thư mục output tổng
        out_size: Kích thước ảnh output (default: 128)
        num_slices: Số slice tạo ra (default: 11)
        log_callback: Function để log (optional)
    
    Returns:
        int: Số slice đã tạo
    """
    # Lấy tên file và loại bỏ phần đuôi để có subject ID
    filename = os.path.basename(brain_file_path)
    subj = filename.replace("_brain.nii.gz", "").replace("_brain.nii", "")
    
    # Log nếu có callback
    if log_callback:
        log_callback(f"[2D] {subj}")

    # Load và chuẩn hóa volume 3D
    vol = load_and_norm(brain_file_path)

    # Tính diện tích não cho mỗi slice theo trục Y (sagittal/coronal tùy canonical)
    # Đếm số voxel não (khác 0) trên mỗi slice
    areas = np.array([np.count_nonzero(vol[:, i, :]) 
                      for i in range(vol.shape[1])])

    # Tìm slice có diện tích não lớn nhất (slice trung tâm)
    center = areas.argmax()

    # Tính toán các slice cần lấy xung quanh slice trung tâm
    # Ví dụ: num_slices=11 thì half=5, lấy 5 slice trước và 5 slice sau center
    half = num_slices // 2
    slice_ids = range(center - half, center + half + 1)

    # Tạo thư mục con cho subject này
    subj_out = os.path.join(output_dir, subj)
    os.makedirs(subj_out, exist_ok=True)

    # Index để đánh số các slice output
    out_idx = 0
    # Duyệt qua các slice đã chọn
    for idx in slice_ids:
        # Bỏ qua nếu index nằm ngoài kích thước volume
        if idx < 0 or idx >= vol.shape[1]:
            continue

        # Lấy slice 2D theo trục Y
        img = vol[:, idx, :]
        # Bỏ qua slice trống (không có não)
        if np.count_nonzero(img) == 0:
            continue

        # Xoay ảnh 90 độ để có hướng đúng
        img = np.rot90(img, 1)
        # Resize về kích thước mong muốn (128x128)
        img = cv2.resize(img, (out_size, out_size))
        # Chuyển từ [0,1] về [0,255] và kiểu uint8 để lưu PNG
        img = (img * 255).astype(np.uint8)

        # Lưu ảnh với tên file có 3 chữ số (000.png, 001.png, ...)
        imageio.imwrite(
            os.path.join(subj_out, f"{out_idx:03d}.png"),
            img
        )
        out_idx += 1
    
    # Trả về số lượng slice đã tạo
    return out_idx

# Chương trình chính
if __name__ == "__main__":
    # Tạo thư mục output nếu chưa tồn tại
    os.makedirs(OUT_DIR, exist_ok=True)

    # Duyệt qua tất cả file trong thư mục skull_stripped
    for f in os.listdir(BRAIN_DIR):
        # Chỉ xử lý các file _brain.nii.gz
        if not f.endswith("_brain.nii.gz"):
            continue

        # Lấy subject ID
        subj = f.replace("_brain.nii.gz", "")
        print(f"[2D] {subj}")
        
        # Xử lý subject thành các slice 2D
        brain_path = os.path.join(BRAIN_DIR, f)
        slice_count = process_subject_to_2d(brain_path, OUT_DIR, OUT_SIZE, NUM_SLICES, print)
        print(f"  -> Generated {slice_count} slices")

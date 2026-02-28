# Import các thư viện cần thiết
import os          # Thao tác với file và thư mục
import numpy as np # Xử lý mảng và tính toán số học
import nibabel as nib  # Đọc file NIfTI (định dạng ảnh não phổ biến)
import cv2         # OpenCV - resize và xử lý ảnh
import imageio     # Lưu ảnh dưới dạng PNG

# ============ CẤU HÌNH ============
# Thư mục chứa các file não đã registration về MNI space (_mni.nii.gz)
# Hoặc dùng skull_stripped nếu chưa có registration
BRAIN_DIR   = r"D:\KhoaLuanTotNghiep\ThucNghiem\mni_registered"
# Thư mục đầu ra để lưu dataset 2D
OUT_DIR     = r"D:\KhoaLuanTotNghiep\Multimodal-Ensemble\data_test\MRI_axial_224x224"
# Kích thước ảnh output (128x128 pixels)
OUT_SIZE    = 224
# Số slice trích xuất từ mỗi subject (nên là số lẻ để có slice trung tâm)
NUM_SLICES  = 11
# ====================================

def load_and_norm(path):
    """
    Load và chuẩn hóa NIfTI volume bằng Z-score trên toàn bộ volume 3D
    
    Chuẩn hóa Z-score trên voxels não (>0) giúp cân bằng độ sáng giữa các subject.
    Sau đó clip Z-score vào [-2, 2] và scale về [0, 1] để có gray level mượt.
    
    Args:
        path: Đường dẫn đến file .nii hoặc .nii.gz
    
    Returns:
        numpy.ndarray: Volume đã được chuẩn hóa về [0, 1] bằng Z-score
    """
    # Đọc file NIfTI
    vol = nib.load(path)
    # Chuyển về dạng canonical (chuẩn hóa hướng) và lấy dữ liệu dạng numpy array
    vol = nib.as_closest_canonical(vol).get_fdata()

    # Lấy các voxel não (giá trị > 0, loại bỏ background)
    brain = vol[vol > 0]
    
    if len(brain) == 0:
        # Nếu không có voxel não, trả về zero volume
        return np.zeros_like(vol)
    
    # Tính mean và std của voxels não
    mean = np.mean(brain)
    std = np.std(brain)
    
    # Áp dụng Z-score chuẩn hóa: (x - mean) / std
    vol = (vol - mean) / (std + 1e-8)
    
    # Clip Z-score vào khoảng [-2, 2] để loại bỏ outliers và có gray level cân đối
    # Điều này giữ các giá trị chính trong khoảng 2 độ lệch chuẩn
    vol = np.clip(vol, -2, 2)
    
    # Scale Z-score từ [-2, 2] về [0, 1]
    # Formula: (z_clipped + 2) / 4
    vol = (vol + 2) / 4

    return vol

def get_brain_bbox(vol):
    """
    Tìm bounding box của vùng não để crop.
    
    Args:
        vol: Volume 3D đã chuẩn hóa
    
    Returns:
        tuple: (x_min, x_max, y_min, y_max, z_min, z_max)
    """
    # Tìm tất cả voxel có giá trị > 0 (vùng não)
    coords = np.argwhere(vol > 0)
    
    if len(coords) == 0:
        # Nếu không có voxel não, trả về toàn bộ volume
        return 0, vol.shape[0], 0, vol.shape[1], 0, vol.shape[2]
    
    # Tìm min/max coordinates
    x_min, y_min, z_min = coords.min(axis=0)
    x_max, y_max, z_max = coords.max(axis=0)
    
    return x_min, x_max, y_min, y_max, z_min, z_max

def process_subject_to_2d(brain_file_path, output_dir, out_size=128, num_slices=11, log_callback=None):
    """
    Xử lý 1 subject từ file _mni.nii.gz (hoặc _brain.nii.gz) thành các slice 2D PNG.
    
    Quy trình:
    1. Load và chuẩn hóa volume 3D
    2. Center crop vùng não (loại bỏ background)
    3. Tìm slice có diện tích não lớn nhất (trục Z - axial)
    4. Lấy các slice xung quanh slice trung tâm
    5. Rotate, resize và lưu thành PNG
    
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
    subj = filename.replace("_mni.nii.gz", "").replace("_brain.nii.gz", "").replace("_mni.nii", "").replace("_brain.nii", "")
    
    # Log nếu có callback
    if log_callback:
        log_callback(f"[2D] {subj}")

    # Load và chuẩn hóa volume 3D
    vol = load_and_norm(brain_file_path)

    # Center crop: Tìm bounding box của não và crop
    x_min, x_max, y_min, y_max, z_min, z_max = get_brain_bbox(vol)
    vol = vol[x_min:x_max, y_min:y_max, z_min:z_max]

    # Tính diện tích não cho mỗi slice theo trục Z (axial - từ trên xuống)
    center = vol.shape[2] // 2

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
        if idx < 0 or idx >= vol.shape[2]:
            continue

        # Lấy slice 2D theo trục Z (axial - từ trên xuống)
        img = vol[:, :, idx]

        # Bỏ qua slice trống (không có não)
        if np.count_nonzero(img) == 0:
            continue
        
        # Xoay ảnh 90 độ để đúng hướng (nếu cần)
        img = np.rot90(img)
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

    # Duyệt qua tất cả file trong thư mục
    for f in os.listdir(BRAIN_DIR):
        # Chỉ xử lý các file _mni.nii.gz, _mni.nii, _brain.nii.gz hoặc _brain.nii
        if not (f.endswith("_mni.nii.gz") or f.endswith("_brain.nii.gz") or 
                f.endswith("_mni.nii") or f.endswith("_brain.nii")):
            continue

        # Lấy subject ID
        subj = f.replace("_mni.nii.gz", "").replace("_brain.nii.gz", "").replace("_mni.nii", "").replace("_brain.nii", "")
        print(f"[2D] {subj}")
        
        # Xử lý subject thành các slice 2D
        brain_path = os.path.join(BRAIN_DIR, f)
        slice_count = process_subject_to_2d(brain_path, OUT_DIR, OUT_SIZE, NUM_SLICES, print)
        print(f"  -> Generated {slice_count} slices")

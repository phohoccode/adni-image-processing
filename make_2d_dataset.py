import os
import numpy as np
import nibabel as nib
import cv2
import imageio

# ============ CONFIG ============
BRAIN_DIR   = r"D:\KhoaLuanTotNghiep\code\skull_stripped"
OUT_DIR     = r"D:\KhoaLuanTotNghiep\code\dataset_2d"
OUT_SIZE    = 128
NUM_SLICES  = 11   # số slice / subject (nên lẻ)
# ================================

def load_and_norm(path):
    """Load và chuẩn hóa NIfTI volume"""
    vol = nib.load(path)
    vol = nib.as_closest_canonical(vol).get_fdata()

    brain = vol[vol > 0]
    p2, p98 = np.percentile(brain, (2, 98))
    vol = np.clip(vol, p2, p98)
    vol = (vol - p2) / (p98 - p2 + 1e-8)

    return vol

def process_subject_to_2d(brain_file_path, output_dir, out_size=128, num_slices=11, log_callback=None):
    """
    Xử lý 1 subject từ file _brain.nii.gz thành các slice 2D PNG.
    
    Args:
        brain_file_path: Đường dẫn đến file _brain.nii.gz
        output_dir: Thư mục output tổng
        out_size: Kích thước ảnh output (default: 128)
        num_slices: Số slice tạo ra (default: 11)
        log_callback: Function để log (optional)
    
    Returns:
        int: Số slice đã tạo
    """
    filename = os.path.basename(brain_file_path)
    subj = filename.replace("_brain.nii.gz", "").replace("_brain.nii", "")
    
    if log_callback:
        log_callback(f"[2D] {subj}")

    vol = load_and_norm(brain_file_path)

    # diện tích não theo trục Y (sagittal/coronal tùy canonical)
    areas = np.array([np.count_nonzero(vol[:, i, :]) 
                      for i in range(vol.shape[1])])

    center = areas.argmax()

    # lấy slice quanh center
    half = num_slices // 2
    slice_ids = range(center - half, center + half + 1)

    subj_out = os.path.join(output_dir, subj)
    os.makedirs(subj_out, exist_ok=True)

    out_idx = 0
    for idx in slice_ids:
        if idx < 0 or idx >= vol.shape[1]:
            continue

        img = vol[:, idx, :]
        if np.count_nonzero(img) == 0:
            continue

        img = np.rot90(img, 1)
        img = cv2.resize(img, (out_size, out_size))
        img = (img * 255).astype(np.uint8)

        imageio.imwrite(
            os.path.join(subj_out, f"{out_idx:03d}.png"),
            img
        )
        out_idx += 1
    
    return out_idx

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    for f in os.listdir(BRAIN_DIR):
        if not f.endswith("_brain.nii.gz"):
            continue

        subj = f.replace("_brain.nii.gz", "")
        print(f"[2D] {subj}")
        
        brain_path = os.path.join(BRAIN_DIR, f)
        slice_count = process_subject_to_2d(brain_path, OUT_DIR, OUT_SIZE, NUM_SLICES, print)
        print(f"  -> Generated {slice_count} slices")

import os
import subprocess


# ============ CONFIG ============
RAW_ADNI_DIR = r"D:\KhoaLuanTotNghiep\test\ADNI"
OUT_DIR      = r"D:\KhoaLuanTotNghiep\code\skull_stripped"
MAX_FOLDERS  = None  # None = xử lý tất cả, hoặc nhập số (ví dụ: 10)
# ================================


def find_nii(subject_dir):
    """Tìm file NIfTI trong thư mục subject"""
    for root, _, files in os.walk(subject_dir):
        for f in files:
            if f.endswith(".nii") or f.endswith(".nii.gz"):
                return os.path.join(root, f)
    return None


def process_skull_stripping(nii_path, output_file, device="cuda", log_callback=None):
    """
    Xử lý loại bỏ sọ cho 1 file NIfTI sử dụng HD-BET.
    
    Args:
        nii_path: Đường dẫn đến file NIfTI gốc
        output_file: Đường dẫn file output
        device: "cuda" hoặc "cpu" (default: "cuda")
        log_callback: Function để log (optional)
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        if log_callback:
            subj = os.path.basename(output_file).replace("_brain.nii.gz", "").replace("_brain.nii", "")
            log_callback(f"[STRIP] {subj}")
        
        result = subprocess.run(
            ["hd-bet", "-i", nii_path, "-o", output_file, "-device", device],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return result.returncode == 0
    except Exception as e:
        if log_callback:
            log_callback(f"[ERROR] {str(e)}")
        return False


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    processed = 0
    for subj in os.listdir(RAW_ADNI_DIR):
        subj_dir = os.path.join(RAW_ADNI_DIR, subj)
        if not os.path.isdir(subj_dir):
            continue

        out_file = os.path.join(OUT_DIR, f"{subj}_brain.nii.gz")
        if os.path.exists(out_file):
            continue  # đã strip

        nii_path = find_nii(subj_dir)
        if nii_path is None:
            print(f"[SKIP] No NII: {subj}")
            continue

        success = process_skull_stripping(nii_path, out_file, "cuda", print)
        
        if success:
            processed += 1
        
        # Kiểm tra giới hạn
        if MAX_FOLDERS is not None and processed >= MAX_FOLDERS:
            print(f"\n[DONE] Đã xử lý {processed} folders (giới hạn: {MAX_FOLDERS})")
            break

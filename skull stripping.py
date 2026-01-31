import os
import subprocess


# ============ CONFIG ============
RAW_ADNI_DIR = r"D:\KhoaLuanTotNghiep\test\ADNI"
OUT_DIR      = r"D:\KhoaLuanTotNghiep\code\skull_stripped"
MAX_FOLDERS  = None  # None = xử lý tất cả, hoặc nhập số (ví dụ: 10)
# ================================

os.makedirs(OUT_DIR, exist_ok=True)


def find_nii(subject_dir):
    for root, _, files in os.walk(subject_dir):
        for f in files:
            if f.endswith(".nii") or f.endswith(".nii.gz"):
                return os.path.join(root, f)
    return None


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

    print(f"[STRIP] {subj}")

    subprocess.run(
        ["hd-bet", "-i", nii_path, "-o", out_file, "-device", "cuda"],
        check=True
    )
    
    # Kiểm tra giới hạn
    if MAX_FOLDERS is not None:
        processed = len([f for f in os.listdir(OUT_DIR) if f.endswith("_brain.nii.gz")])
        if processed >= MAX_FOLDERS:
            print(f"\n[DONE] Đã xử lý {processed} folders (giới hạn: {MAX_FOLDERS})")
            break

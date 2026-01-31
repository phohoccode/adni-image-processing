import os
import numpy as np
import nibabel as nib
import cv2
import imageio

# ============ CONFIG ============
BRAIN_DIR   = r"D:\KhoaLuanTotNghiep\code\skull_stripped"
OUT_DIR     = r"D:\KhoaLuanTotNghiep\code\dataset_2d"

OUT_SIZE    = 128
# ================================

os.makedirs(OUT_DIR, exist_ok=True)


def load_and_norm(path):
    vol = nib.load(path)
    vol = nib.as_closest_canonical(vol).get_fdata()
    brain = vol[vol > 0]
    p2, p98 = np.percentile(brain, (2, 98))
    vol = np.clip(vol, p2, p98)
    return (vol - p2) / (p98 - p2 + 1e-8)


for f in os.listdir(BRAIN_DIR):
    if not f.endswith("_brain.nii.gz"):
        continue

    subj = f.replace("_brain.nii.gz", "")
    print(f"[2D] {subj}")

    vol = load_and_norm(os.path.join(BRAIN_DIR, f))

    areas = [np.count_nonzero(vol[:, i, :]) for i in range(vol.shape[1])]
    best = np.argmax(areas)

    img = vol[:, best, :]
    img = np.rot90(img, k=1)  # Xoay 90 độ ngược chiều kim đồng hồ
    img = cv2.resize(img, (OUT_SIZE, OUT_SIZE))
    img = (img * 255).astype(np.uint8)

    subj_out = os.path.join(OUT_DIR, subj)
    os.makedirs(subj_out, exist_ok=True)

    imageio.imwrite(os.path.join(subj_out, "000.png"), img)



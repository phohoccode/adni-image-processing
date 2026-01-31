import os
import shutil
import pandas as pd

# ============ CONFIG ============
DATASET_2D = r"D:\KhoaLuanTotNghiep\code\dataset_2d"
CSV_PATH   = r"D:\KhoaLuanTotNghiep\ADNIMERGE_30Jan2026.csv"
OUT_DIR    = r"D:\KhoaLuanTotNghiep\code\dataset_labeled"
# ================================

os.makedirs(OUT_DIR, exist_ok=True)

# Load labels
df = pd.read_csv(CSV_PATH)
df = df[["PTID", "DX"]].dropna()
df = df.drop_duplicates("PTID")
label_map = dict(zip(df.PTID, df.DX))

for subj in os.listdir(DATASET_2D):
    subj_dir = os.path.join(DATASET_2D, subj)
    if not os.path.isdir(subj_dir):
        continue

    if subj not in label_map:
        continue

    label = label_map[subj]
    out_label_dir = os.path.join(OUT_DIR, label)
    os.makedirs(out_label_dir, exist_ok=True)

    # Copy ảnh trực tiếp vào folder label với tên là subject.png
    img_src = os.path.join(subj_dir, "000.png")
    if os.path.exists(img_src):
        img_dst = os.path.join(out_label_dir, f"{subj}.png")
        shutil.copy2(img_src, img_dst)

print("Done.")

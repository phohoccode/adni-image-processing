import pandas as pd
import os
import numpy as np

# ================= CẤU HÌNH =================
# Đường dẫn file gốc tải từ ADNI (thường là ADNIMERGE.csv)
RAW_CSV_PATH = r"D:\KhoaLuanTotNghiep\ThucNghiem\ADNIMERGE.csv" 

# Đường dẫn folder ảnh 2D đã tạo (để đối chiếu xem ai có ảnh)
IMAGE_DIR = r"D:\KhoaLuanTotNghiep\ThucNghiem\dataset_2d_7"

# Đường dẫn lưu file sạch
OUTPUT_CSV = r"D:\KhoaLuanTotNghiep\ThucNghiem\final_dataset_2.csv"
# ============================================

def clean_data():
    print("Đang đọc file CSV gốc...")
    df = pd.read_csv(RAW_CSV_PATH, low_memory=False)
    
    # 1. Chỉ lấy dòng Baseline (lần khám đầu tiên)
    # Cột VISCODE chứa mã lần khám, 'bl' là baseline
    df = df[df['VISCODE'] == 'bl'].copy()
    print(f"-> Số lượng dòng Baseline: {len(df)}")

    # 2. Chọn các cột quan trọng
    # PTID: ID bệnh nhân
    # DX_bl: Chẩn đoán gốc (CN, AD, LMCI, EMCI...)
    # AGE, PTGENDER, PTEDUCAT: Thông tin nhân khẩu
    # APOE4, MMSE, CDR: Chỉ số lâm sàng
    cols_to_keep = ['PTID', 'DX_bl', 'AGE', 'PTGENDER', 'PTEDUCAT', 'APOE4', 'MMSE']
    df = df[cols_to_keep]

    # 3. Đổi tên cột cho dễ code
    df = df.rename(columns={'PTID': 'Subject_ID', 'PTGENDER': 'Gender'})

    # 4. Xử lý dữ liệu NHÃN (Label)
    # Chỉ lấy 3 nhóm: CN, LMCI, AD
    mapping_dict = {
        'CN': 0,       # Nhóm bình thường
        'LMCI': 1,     # Nhóm suy giảm nhận thức nhẹ
        'AD': 2        # Nhóm bệnh Alzheimer
    }
    df['Label'] = df['DX_bl'].map(mapping_dict)
    
    # Bỏ những dòng không có nhãn (NaN)
    df = df.dropna(subset=['Label'])

    # 5. Xử lý cột Giới tính (Gender)
    # Male -> 0, Female -> 1
    df['Gender'] = df['Gender'].replace({'Male': 0, 'Female': 1})

    # 6. Xử lý giá trị thiếu (Missing Values) ở các cột lâm sàng
    # Cách đơn giản nhất cho khóa luận: Bỏ dòng có NaN
    clinical_cols = ['AGE', 'Gender', 'APOE4', 'MMSE']
    # Ép kiểu về số (đề phòng bị lẫn chữ)
    for col in clinical_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=clinical_cols)
    print(f"-> Số lượng dòng sau khi lọc NaN: {len(df)}")

    # 7. QUAN TRỌNG NHẤT: Chỉ giữ lại bệnh nhân CÓ ẢNH trong folder
    # Lấy danh sách ID từ tên folder ảnh
    available_ids = [d for d in os.listdir(IMAGE_DIR) if os.path.isdir(os.path.join(IMAGE_DIR, d))]
    print(f"-> Tìm thấy {len(available_ids)} thư mục ảnh.")
    
    # Lọc DataFrame chỉ giữ lại ID có trong danh sách ảnh
    df = df[df['Subject_ID'].isin(available_ids)]
    
    # Reset index
    df = df.reset_index(drop=True)
    
    print(f"==> KẾT QUẢ CUỐI CÙNG: {len(df)} bệnh nhân (Có đủ cả Ảnh và Số liệu).")

    # 8. Lưu file
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Đã lưu file sạch tại: {OUTPUT_CSV}")

if __name__ == "__main__":
    clean_data()
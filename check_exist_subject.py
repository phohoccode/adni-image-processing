def check_folder_exists_in_adni(folder_name, adni_path=r"D:\KhoaLuanTotNghiep\ThucNghiem\ADNI"):
    """
    Kiểm tra xem một thư mục có tồn tại trong thư mục ADNI không
    
    Args:
        folder_name (str): Tên thư mục cần kiểm tra
        adni_path (str): Đường dẫn đến thư mục ADNI (mặc định là test\ADNI)
    
    Returns:
        bool: True nếu tồn tại, False nếu không
    """
    from pathlib import Path
    adni_folder = Path(adni_path)
    target_folder = adni_folder / folder_name
    return target_folder.exists() and target_folder.is_dir()


def get_all_folders_in_adni(adni_path=r"D:\KhoaLuanTotNghiep\ThucNghiem\ADNI"):
    """
    Lấy danh sách tất cả các thư mục cấp 1 trong ADNI
    
    Args:
        adni_path (str): Đường dẫn đến thư mục ADNI
    
    Returns:
        set: Tập hợp tên các thư mục
    """
    from pathlib import Path
    adni_folder = Path(adni_path)
    return {p.name for p in adni_folder.iterdir() if p.is_dir()}


# Ví dụ sử dụng
if __name__ == "__main__":
    print("\n--- Kiểm tra thư mục trong ADNI ---")
    print("(Nhấn Enter để thoát)\n")
    
    while True:
        # Nhập tên các thư mục từ terminal (cách nhau bởi khoảng trắng)
        user_input = input("Nhập tên các thư mục (cách nhau bởi khoảng trắng): ")
        
        # Tách các tên thư mục
        folder_names = user_input.strip().split()
        
        # Nếu không nhập gì (chỉ Enter) thì thoát
        if not folder_names or (len(folder_names) == 1 and folder_names[0] == ""):
            print("\nĐã thoát!")
            break
        
        # Kiểm tra và hiển thị kết quả
        print(f"\n--- Kết quả kiểm tra ({len(folder_names)} thư mục) ---")
        for folder in folder_names:
            exists = check_folder_exists_in_adni(folder)
            status = "✓ TỒN TẠI" if exists else "✗ KHÔNG TỒN TẠI"
            print(f"{folder}: {status}")
        print()  # Dòng trống để dễ đọc


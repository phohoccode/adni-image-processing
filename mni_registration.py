# Import các thư viện cần thiết
import os
import subprocess
import nibabel as nib
from pathlib import Path
import platform


def windows_to_wsl_path(windows_path):
    """
    Chuyển đổi đường dẫn Windows sang định dạng WSL.
    Ví dụ: D:\\folder\\file.txt -> /mnt/d/folder/file.txt
    
    Args:
        windows_path: Đường dẫn Windows (str hoặc Path)
    
    Returns:
        str: Đường dẫn WSL format
    """
    path_str = str(windows_path)
    # Chuyển backslash thành forward slash
    path_str = path_str.replace('\\', '/')
    
    # Xử lý drive letter (C:, D:, etc.)
    if len(path_str) >= 2 and path_str[1] == ':':
        drive = path_str[0].lower()
        rest = path_str[2:]
        return f"/mnt/{drive}{rest}"
    
    return path_str


# Thư mục chứa các file đã loại bỏ skull
SKULL_STRIPPED_DIR = r"D:\KhoaLuanTotNghiep\ThucNghiem\skull_stripped"
# Thư mục đầu ra để lưu các file đã registration
OUT_DIR = r"D:\KhoaLuanTotNghiep\ThucNghiem\mni_registered"
# Đường dẫn MNI template trong WSL
MNI_TEMPLATE_WSL = "/home/phohoccode/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz"
# Độ phân giải output (1mm isotropic là chuẩn)
OUTPUT_RESOLUTION = (1.0, 1.0, 1.0)
# ====================================


def check_fsl_installed():
    """
    Kiểm tra xem FSL đã được cài đặt trong WSL chưa.
    
    Returns:
        bool: True nếu FSL đã cài đặt, False nếu chưa
    """
    try:
        # Chạy flirt qua WSL Ubuntu-22.04 với user phohoccode và set FSLDIR
        result = subprocess.run(
            ["wsl", "-d", "Ubuntu-22.04", "-u", "phohoccode", "bash", "-c", 
             "export FSLDIR=/home/phohoccode/fsl; "
             "source /home/phohoccode/fsl/etc/fslconf/fsl.sh; "
             "flirt -version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def register_to_mni(input_file, output_file, template=MNI_TEMPLATE_WSL, log_callback=None):
    """
    Đăng ký (register) ảnh não về không gian MNI152 chuẩn sử dụng FSL FLIRT qua WSL.
    
    Quy trình:
    1. Affine registration (12 DOF: translation, rotation, scale, shear)
    2. Resample về độ phân giải 1mm isotropic
    3. Căn chỉnh về hệ tọa độ MNI standard
    
    Args:
        input_file: Đường dẫn Windows đến file _brain.nii.gz (đã skull stripping)
        output_file: Đường dẫn Windows file output (_mni.nii.gz)
        template: Đường dẫn WSL đến MNI template (default: $FSLDIR/data/standard/MNI152_T1_1mm_brain.nii.gz)
        log_callback: Function để log (optional)
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    try:
        if log_callback:
            subj = os.path.basename(output_file).replace("_mni.nii.gz", "")
            log_callback(f"[MNI] {subj}")
        
        # Tạo thư mục output nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # File ma trận transformation (lưu để có thể apply cho các ảnh khác)
        matrix_file = output_file.replace("_mni.nii.gz", "_mni.mat")
        
        # Chuyển đổi đường dẫn Windows sang WSL format
        input_wsl = windows_to_wsl_path(input_file)
        output_wsl = windows_to_wsl_path(output_file)
        matrix_wsl = windows_to_wsl_path(matrix_file)
        
        # Chạy FSL FLIRT cho affine registration qua WSL
        # -in: input file
        # -ref: reference template (MNI152)
        # -out: output registered file
        # -omat: output transformation matrix
        # -bins 256: số histogram bins (tốt cho T1-weighted)
        # -cost corratio: correlation ratio cost function (tốt cho intra-modal)
        # -searchrx -90 90: search range cho rotation về X axis
        # -searchry -90 90: search range cho rotation về Y axis
        # -searchrz -90 90: search range cho rotation về Z axis
        # -dof 12: 12 degrees of freedom (affine transform)
        # -interp trilinear: trilinear interpolation
        
        # Build FLIRT command - set FSLDIR và source fsl.sh
        flirt_cmd = (
            f"export FSLDIR=/home/phohoccode/fsl; "
            f"source /home/phohoccode/fsl/etc/fslconf/fsl.sh; "
            f"flirt "
            f"-in '{input_wsl}' "
            f"-ref '{template}' "
            f"-out '{output_wsl}' "
            f"-omat '{matrix_wsl}' "
            f"-bins 256 "
            f"-cost corratio "
            f"-searchrx -90 90 "
            f"-searchry -90 90 "
            f"-searchrz -90 90 "
            f"-dof 12 "
            f"-interp trilinear"
        )
        
        # Chạy qua WSL Ubuntu-22.04 với user phohoccode
        result = subprocess.run(
            ["wsl", "-d", "Ubuntu-22.04", "-u", "phohoccode", "bash", "-c", flirt_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300  # 5 phút timeout
        )
        
        if result.returncode != 0:
            if log_callback:
                log_callback(f"[ERROR] FLIRT failed: {result.stderr}")
            return False
        
        # Kiểm tra xem file output có được tạo không
        if not os.path.exists(output_file):
            if log_callback:
                log_callback(f"[ERROR] Output file not created")
            return False
        
        # Verify output resolution
        img = nib.load(output_file)
        voxel_size = img.header.get_zooms()
        if log_callback:
            log_callback(f"  -> Voxel size: {voxel_size[0]:.2f}x{voxel_size[1]:.2f}x{voxel_size[2]:.2f}mm")
        
        return True
        
    except Exception as e:
        if log_callback:
            log_callback(f"[ERROR] {str(e)}")
        return False


def check_template_exists():
    """
    Kiểm tra xem MNI template có tồn tại trong WSL không.
    
    Returns:
        bool: True nếu template tồn tại
    """
    try:
        # Kiểm tra file tồn tại trong WSL Ubuntu-22.04 với user phohoccode
        result = subprocess.run(
            ["wsl", "-d", "Ubuntu-22.04", "-u", "phohoccode", "bash", "-c", 
             "export FSLDIR=/home/phohoccode/fsl; "
             "source /home/phohoccode/fsl/etc/fslconf/fsl.sh; "
             f"test -f {MNI_TEMPLATE_WSL} && echo 'exists'"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        return "exists" in result.stdout
    except:
        return False


# Chương trình chính
if __name__ == "__main__":
    # Kiểm tra FSL đã cài đặt
    if not check_fsl_installed():
        print("[ERROR] FSL chưa được cài đặt trong WSL hoặc WSL chưa được cài đặt")
        print("Vui lòng:")
        print("  1. Cài WSL: wsl --install -d Ubuntu-22.04")
        print("  2. Cài FSL trong WSL: https://fsl.fmrib.ox.ac.uk/fsl/docs/install/linux.html")
        exit(1)
    
    # Kiểm tra template tồn tại
    if not check_template_exists():
        print(f"[ERROR] MNI template không tồn tại: {MNI_TEMPLATE_WSL}")
        print("Vui lòng đảm bảo FSL đã được cài đặt đúng trong WSL")
        print("Chạy trong WSL: ls $FSLDIR/data/standard/MNI152_T1_1mm_brain.nii.gz")
        exit(1)
    
    print(f"Using MNI template: {MNI_TEMPLATE_WSL}")
    
    # Tạo thư mục output
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Lấy danh sách các file đã skull stripping
    brain_files = [f for f in os.listdir(SKULL_STRIPPED_DIR) 
                   if f.endswith("_brain.nii.gz")]
    
    print(f"Found {len(brain_files)} subjects to register")
    print("=" * 60)
    
    # Xử lý từng subject
    success_count = 0
    failed_subjects = []
    
    for i, brain_file in enumerate(brain_files, 1):
        input_path = os.path.join(SKULL_STRIPPED_DIR, brain_file)
        subj_id = brain_file.replace("_brain.nii.gz", "")
        output_path = os.path.join(OUT_DIR, f"{subj_id}_mni.nii.gz")
        
        print(f"[{i}/{len(brain_files)}] Processing: {subj_id}")
        
        # Bỏ qua nếu đã xử lý
        if os.path.exists(output_path):
            print(f"  -> Already exists, skipping")
            success_count += 1
            continue
        
        # Thực hiện registration
        success = register_to_mni(input_path, output_path, MNI_TEMPLATE_WSL, print)
        
        if success:
            success_count += 1
            print(f"  ✓ Success")
        else:
            failed_subjects.append(subj_id)
            print(f"  ✗ Failed")
        
        print("-" * 60)
    
    # Tóm tắt kết quả
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total subjects: {len(brain_files)}")
    print(f"Successfully registered: {success_count}")
    print(f"Failed: {len(failed_subjects)}")
    
    if failed_subjects:
        print("\nFailed subjects:")
        for subj in failed_subjects:
            print(f"  - {subj}")

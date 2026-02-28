import os
import hashlib
from collections import defaultdict
from pathlib import Path
import argparse


def get_file_hash(file_path):
    """
    Tính hash MD5 của file để kiểm tra trùng lặp
    
    Args:
        file_path: Đường dẫn đến file
    
    Returns:
        str: Hash MD5 của file
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Lỗi khi đọc file {file_path}: {e}")
        return None


def count_duplicate_files(adni_dir, check_by_content=False):
    """
    Đếm số file trùng và không trùng trong thư mục ADNI
    
    Args:
        adni_dir: Đường dẫn đến thư mục ADNI
        check_by_content: True = kiểm tra theo nội dung (hash), False = kiểm tra theo tên file
    
    Returns:
        dict: Kết quả phân tích
    """
    
    print(f"Đang quét thư mục: {adni_dir}")
    print(f"Phương pháp: {'Theo nội dung file (hash)' if check_by_content else 'Theo tên file'}\n")
    
    if not os.path.exists(adni_dir):
        print(f"Lỗi: Thư mục {adni_dir} không tồn tại!")
        return None
    
    # Dictionary để lưu trữ file theo tên hoặc hash
    file_dict = defaultdict(list)
    total_files = 0
    total_subjects = 0
    subject_file_counts = {}
    
    # Quét tất cả các thư mục subject
    for subject in os.listdir(adni_dir):
        subject_path = os.path.join(adni_dir, subject)
        
        if not os.path.isdir(subject_path):
            continue
        
        total_subjects += 1
        file_count = 0
        
        # Quét tất cả file trong thư mục subject
        for file_name in os.listdir(subject_path):
            file_path = os.path.join(subject_path, file_name)
            
            if not os.path.isfile(file_path):
                continue
            
            file_count += 1
            total_files += 1
            
            # Xác định key để kiểm tra trùng
            if check_by_content:
                key = get_file_hash(file_path)
                if key is None:
                    continue
            else:
                key = file_name  # Chỉ kiểm tra theo tên file
            
            file_dict[key].append({
                'subject': subject,
                'file_name': file_name,
                'file_path': file_path,
                'size': os.path.getsize(file_path)
            })
        
        subject_file_counts[subject] = file_count
        
        if total_subjects % 100 == 0:
            print(f"Đã quét {total_subjects} subjects, {total_files} files...")
    
    print(f"\nHoàn thành! Đã quét {total_subjects} subjects, {total_files} files")
    
    # Phân tích file trùng
    unique_files = []  # File không trùng (chỉ xuất hiện 1 lần)
    duplicate_groups = []  # Nhóm file trùng (xuất hiện >= 2 lần)
    
    for key, files in file_dict.items():
        if len(files) == 1:
            unique_files.append(files[0])
        else:
            duplicate_groups.append(files)
    
    # Tính tổng số file trong các nhóm trùng
    total_duplicate_files = sum(len(group) for group in duplicate_groups)
    
    return {
        'total_files': total_files,
        'total_subjects': total_subjects,
        'unique_files': unique_files,
        'duplicate_groups': duplicate_groups,
        'total_unique': len(unique_files),
        'total_duplicate_files': total_duplicate_files,
        'duplicate_group_count': len(duplicate_groups),
        'subject_file_counts': subject_file_counts,
        'check_by_content': check_by_content
    }


def print_results(results):
    """In kết quả ra màn hình"""
    if results is None:
        return
    
    print("\n" + "="*70)
    print("KẾT QUẢ PHÂN TÍCH FILE TRÙNG LẶP")
    print("="*70)
    
    print(f"\nPhương pháp kiểm tra: {'Theo nội dung file (MD5 hash)' if results['check_by_content'] else 'Theo tên file'}")
    
    print(f"\nTổng số subjects: {results['total_subjects']}")
    print(f"Tổng số files: {results['total_files']}")
    
    print("\n" + "-"*70)
    print(f"FILE KHÔNG TRÙNG (unique): {results['total_unique']} files")
    print(f"FILE TRÙNG LẶP: {results['total_duplicate_files']} files trong {results['duplicate_group_count']} nhóm")
    print("-"*70)
    
    if results['total_files'] > 0:
        unique_percent = (results['total_unique'] / results['total_files']) * 100
        duplicate_percent = (results['total_duplicate_files'] / results['total_files']) * 100
        print(f"\nTỷ lệ file không trùng: {unique_percent:.2f}%")
        print(f"Tỷ lệ file trùng lặp: {duplicate_percent:.2f}%")
    
    # Hiển thị một số nhóm file trùng
    if results['duplicate_groups']:
        print("\n" + "-"*70)
        print("MỘT SỐ NHÓM FILE TRÙNG LẶP (Top 10):")
        print("-"*70)
        
        # Sắp xếp theo số lượng file trong nhóm
        sorted_groups = sorted(results['duplicate_groups'], key=lambda x: len(x), reverse=True)
        
        for i, group in enumerate(sorted_groups[:10], 1):
            print(f"\nNhóm {i}: {len(group)} files trùng nhau")
            print(f"  Tên file: {group[0]['file_name']}")
            print(f"  Kích thước: {group[0]['size']} bytes")
            print(f"  Xuất hiện ở các subjects:")
            for file_info in group[:5]:  # Hiển thị tối đa 5 subjects
                print(f"    - {file_info['subject']}")
            if len(group) > 5:
                print(f"    ... và {len(group) - 5} subject khác")
    
    # Thống kê số file theo subject
    file_counts = list(results['subject_file_counts'].values())
    if file_counts:
        print("\n" + "-"*70)
        print("THỐNG KÊ SỐ FILE THEO SUBJECT:")
        print("-"*70)
        print(f"  Số file ít nhất: {min(file_counts)} files")
        print(f"  Số file nhiều nhất: {max(file_counts)} files")
        print(f"  Trung bình: {sum(file_counts)/len(file_counts):.1f} files/subject")
    
    print("\n" + "="*70)


def export_results(results, output_file):
    """Xuất kết quả ra file CSV"""
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nhóm', 'Tên file', 'Số lượng trùng', 'Subject', 'Đường dẫn', 'Kích thước (bytes)'])
        
        for i, group in enumerate(results['duplicate_groups'], 1):
            for file_info in group:
                writer.writerow([
                    i,
                    file_info['file_name'],
                    len(group),
                    file_info['subject'],
                    file_info['file_path'],
                    file_info['size']
                ])
    
    print(f"\nĐã xuất danh sách file trùng ra: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Đếm số file trùng và không trùng trong thư mục ADNI'
    )
    
    parser.add_argument(
        '--adni_dir',
        type=str,
        default='../ThucNghiem/ADNI',
        help='Đường dẫn đến thư mục ADNI (mặc định: ../ThucNghiem/ADNI)'
    )
    
    parser.add_argument(
        '--by_content',
        action='store_true',
        help='Kiểm tra trùng theo nội dung file (hash) thay vì tên file'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        help='Xuất danh sách file trùng ra file CSV (ví dụ: duplicates.csv)'
    )
    
    args = parser.parse_args()
    
    # Chạy phân tích
    results = count_duplicate_files(args.adni_dir, args.by_content)
    
    # In kết quả
    print_results(results)
    
    # Xuất ra file nếu được yêu cầu
    if args.export and results and results['duplicate_groups']:
        export_results(results, args.export)
    elif args.export and results and not results['duplicate_groups']:
        print(f"\nKhông có file trùng lặp để xuất!")


if __name__ == '__main__':
    main()

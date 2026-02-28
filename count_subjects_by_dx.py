import os
import pandas as pd
from collections import Counter
import argparse


def count_subjects_by_dx(adni_dir, csv_file):
    """
    Đếm số lượng subject trong thư mục ADNI theo từng loại DX_bl
    
    Args:
        adni_dir: Đường dẫn đến thư mục ADNI chứa các subject
        csv_file: Đường dẫn đến file CSV chứa thông tin DX_bl
    
    Returns:
        dict: Dictionary chứa số lượng subject theo từng DX_bl
    """
    
    # Đọc file CSV
    print(f"Đang đọc file CSV: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # Lấy danh sách các subject từ thư mục ADNI
    print(f"\nĐang quét thư mục: {adni_dir}")
    subjects_in_dir = []
    
    if not os.path.exists(adni_dir):
        print(f"Lỗi: Thư mục {adni_dir} không tồn tại!")
        return None
    
    for item in os.listdir(adni_dir):
        item_path = os.path.join(adni_dir, item)
        if os.path.isdir(item_path):
            subjects_in_dir.append(item)
    
    print(f"Tìm thấy {len(subjects_in_dir)} subject trong thư mục ADNI")
    
    # Lọc DataFrame chỉ lấy các subject có trong thư mục
    # PTID trong CSV có format như '011_S_0002'
    df_filtered = df[df['PTID'].isin(subjects_in_dir)]
    
    # Lấy DX_bl duy nhất cho mỗi subject (mỗi subject chỉ có 1 DX_bl)
    df_unique = df_filtered[['PTID', 'DX_bl']].drop_duplicates(subset=['PTID'])
    
    print(f"Có {len(df_unique)} subject được tìm thấy trong file CSV")
    
    # Đếm số lượng theo từng DX_bl
    dx_counts = df_unique['DX_bl'].value_counts().to_dict()
    
    # Tìm các subject không có trong CSV
    subjects_not_in_csv = set(subjects_in_dir) - set(df_unique['PTID'].tolist())
    
    return {
        'dx_counts': dx_counts,
        'total_subjects_in_dir': len(subjects_in_dir),
        'total_subjects_in_csv': len(df_unique),
        'subjects_not_in_csv': sorted(list(subjects_not_in_csv))
    }


def print_results(results):
    """In kết quả ra màn hình"""
    if results is None:
        return
    
    print("\n" + "="*60)
    print("KẾT QUẢ PHÂN TÍCH")
    print("="*60)
    
    print(f"\nTổng số subject trong thư mục ADNI: {results['total_subjects_in_dir']}")
    print(f"Số subject tìm thấy trong CSV: {results['total_subjects_in_csv']}")
    
    print("\n" + "-"*60)
    print("SỐ LƯỢNG SUBJECT THEO TỪNG LOẠI DX_bl:")
    print("-"*60)
    
    dx_counts = results['dx_counts']
    total = sum(dx_counts.values())
    
    # Sắp xếp theo số lượng giảm dần
    for dx, count in sorted(dx_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        print(f"{dx:20s}: {count:4d} subjects ({percentage:5.2f}%)")
    
    print("-"*60)
    print(f"{'TỔNG':20s}: {total:4d} subjects (100.00%)")
    
    # Hiển thị các subject không có trong CSV
    if results['subjects_not_in_csv']:
        print("\n" + "-"*60)
        print(f"Có {len(results['subjects_not_in_csv'])} subject KHÔNG tìm thấy trong CSV:")
        print("-"*60)
        for subject in results['subjects_not_in_csv'][:10]:  # Hiển thị tối đa 10 subject
            print(f"  - {subject}")
        if len(results['subjects_not_in_csv']) > 10:
            print(f"  ... và {len(results['subjects_not_in_csv']) - 10} subject khác")
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Đếm số lượng subject trong thư mục ADNI theo từng loại DX_bl'
    )
    
    parser.add_argument(
        '--adni_dir',
        type=str,
        default='../ThucNghiem/ADNI',
        help='Đường dẫn đến thư mục ADNI (mặc định: ../ThucNghiem/ADNI)'
    )
    
    parser.add_argument(
        '--csv_file',
        type=str,
        default='../ThucNghiem/ADNIMERGE.csv',
        help='Đường dẫn đến file CSV (mặc định: ../ThucNghiem/ADNIMERGE.csv)'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        help='Xuất kết quả ra file CSV (ví dụ: results.csv)'
    )
    
    args = parser.parse_args()
    
    # Chạy phân tích
    results = count_subjects_by_dx(args.adni_dir, args.csv_file)
    
    # In kết quả
    print_results(results)
    
    # Xuất ra file nếu được yêu cầu
    if args.export and results:
        df_export = pd.DataFrame([
            {'DX_bl': dx, 'Count': count} 
            for dx, count in results['dx_counts'].items()
        ])
        df_export.to_csv(args.export, index=False)
        print(f"\nĐã xuất kết quả ra file: {args.export}")


if __name__ == '__main__':
    main()

import os
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split
import random
from collections import defaultdict

def split_dataset_by_subject(
    source_dir=r"D:\KhoaLuanTotNghiep\code\dataset_labeled",
    output_dir=r"D:\KhoaLuanTotNghiep\test\dataset_split",
    train_ratio=0.70,
    val_ratio=0.15,
    test_ratio=0.15,
    random_seed=42
):
    """
    Chia dữ liệu theo subject-level split.
    
    Args:
        source_dir: Thư mục chứa dữ liệu đã gán nhãn (CN, MCI, Dementia)
        output_dir: Thư mục đích chứa train/val/test
        train_ratio: Tỷ lệ tập train (0.70 = 70%)
        val_ratio: Tỷ lệ tập validation (0.15 = 15%)
        test_ratio: Tỷ lệ tập test (0.15 = 15%)
        random_seed: Seed cho random để đảm bảo reproducibility
    """
    
    # Kiểm tra tỷ lệ
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, "Tổng các tỷ lệ phải bằng 1.0"
    
    # Set random seed
    random.seed(random_seed)
    
    print("=" * 70)
    print("CHIA DỮ LIỆU THEO SUBJECT-LEVEL SPLIT")
    print("=" * 70)
    print(f"Thư mục nguồn: {source_dir}")
    print(f"Thư mục đích: {output_dir}")
    print(f"Tỷ lệ - Train: {train_ratio*100:.1f}% | Val: {val_ratio*100:.1f}% | Test: {test_ratio*100:.1f}%")
    print(f"Random seed: {random_seed}")
    print("=" * 70)
    
    # Danh sách các nhãn (labels)
    labels = ["CN", "MCI", "Dementia"]
    
    # Kiểm tra thư mục nguồn
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Không tìm thấy thư mục nguồn: {source_dir}")
    
    # Thu thập thông tin về subjects theo từng label
    subjects_by_label = defaultdict(list)
    subject_files_map = defaultdict(lambda: defaultdict(list))  # {label: {subject_id: [files]}}
    
    for label in labels:
        label_dir = os.path.join(source_dir, label)
        if not os.path.exists(label_dir):
            print(f"[WARNING] Không tìm thấy thư mục: {label}")
            continue
        
        # Lấy danh sách tất cả các file ảnh
        image_files = [f for f in os.listdir(label_dir) if f.endswith('.png')]
        
        # Trích xuất subject ID từ tên file
        # Format có thể là: {subject_id}.png hoặc {subject_id}_slice{num}.png
        subjects = set()
        for img_file in image_files:
            # Lấy subject ID (phần trước .png, và trước _slice nếu có)
            subject_id = img_file.replace('.png', '')
            
            # Nếu có _slice hoặc số ở cuối, loại bỏ để lấy subject ID thuần
            # Format ADNI thường là: XXX_S_XXXX
            # Ví dụ: 003_S_1059.png, 003_S_1059_001.png, 003_S_1059_slice1.png
            parts = subject_id.split('_')
            if len(parts) >= 3:
                # Lấy 3 phần đầu: 003_S_1059
                subject_id = '_'.join(parts[:3])
            
            subjects.add(subject_id)
            subject_files_map[label][subject_id].append(img_file)
        
        subjects_by_label[label] = sorted(list(subjects))
        
        # Đếm tổng số file
        total_files = sum(len(files) for files in subject_files_map[label].values())
        print(f"[{label}] Tìm thấy {len(subjects_by_label[label])} bệnh nhân với {total_files} ảnh")
    
    print("\n" + "=" * 70)
    print("CHIA TẬP DỮ LIỆU")
    print("=" * 70)
    
    # Chia subjects cho từng label
    splits = {
        'train': defaultdict(list),
        'validation': defaultdict(list),
        'test': defaultdict(list)
    }
    
    for label in labels:
        if label not in subjects_by_label or len(subjects_by_label[label]) == 0:
            continue
        
        subjects = subjects_by_label[label]
        n_subjects = len(subjects)
        
        # Shuffle subjects trước
        random.shuffle(subjects)
        
        # Xử lý trường hợp đặc biệt: số subjects quá ít
        if n_subjects < 3:
            # Nếu chỉ có 1-2 subjects, đặt tất cả vào train
            train_subjects = subjects
            val_subjects = []
            test_subjects = []
            print(f"[WARNING] {label} chỉ có {n_subjects} subject(s), đặt tất cả vào train")
        else:
            # Chia subjects sử dụng train_test_split để đảm bảo tỷ lệ chính xác
            # Bước 1: Tách train và (val+test)
            train_subjects, temp_subjects = train_test_split(
                subjects, 
                train_size=train_ratio, 
                random_state=random_seed
            )
            
            # Bước 2: Tách val và test từ temp
            if len(temp_subjects) < 2:
                # Nếu phần còn lại chỉ có 1 subject, đặt vào test
                val_subjects = []
                test_subjects = temp_subjects
            else:
                # Tính tỷ lệ val trong phần còn lại
                val_ratio_adjusted = val_ratio / (val_ratio + test_ratio)
                val_subjects, test_subjects = train_test_split(
                    temp_subjects, 
                    train_size=val_ratio_adjusted, 
                    random_state=random_seed
                )
        
        splits['train'][label] = train_subjects
        splits['validation'][label] = val_subjects
        splits['test'][label] = test_subjects
        
        n_subjects = len(subjects)
        print(f"\n[{label}]")
        print(f"  Tổng subjects: {n_subjects}")
        print(f"  Train:      {len(train_subjects)} subjects ({len(train_subjects)/n_subjects*100:.1f}%)")
        print(f"  Validation: {len(val_subjects)} subjects ({len(val_subjects)/n_subjects*100:.1f}%)")
        print(f"  Test:       {len(test_subjects)} subjects ({len(test_subjects)/n_subjects*100:.1f}%)")
        
        # Đếm số lượng ảnh cho mỗi split
        train_images = sum(len(subject_files_map[label][sid]) for sid in train_subjects)
        val_images = sum(len(subject_files_map[label][sid]) for sid in val_subjects)
        test_images = sum(len(subject_files_map[label][sid]) for sid in test_subjects)
        print(f"  → Train:      {train_images} ảnh")
        print(f"  → Validation: {val_images} ảnh")
        print(f"  → Test:       {test_images} ảnh")
    
    print("\n" + "=" * 70)
    print("SAO CHÉP DỮ LIỆU")
    print("=" * 70)
    
    # Tạo cấu trúc thư mục và sao chép files
    total_copied = 0
    
    for split_name, label_subjects in splits.items():
        print(f"\n[{split_name.upper()}]")
        
        for label, subjects in label_subjects.items():
            if len(subjects) == 0:
                continue
            
            # Tạo thư mục đích
            dest_label_dir = os.path.join(output_dir, split_name, label)
            os.makedirs(dest_label_dir, exist_ok=True)
            
            # Sao chép files
            source_label_dir = os.path.join(source_dir, label)
            copied = 0
            
            for subject_id in subjects:
                # Lấy TẤT CẢ các file của subject này
                subject_files = subject_files_map[label].get(subject_id, [])
                
                for img_file in subject_files:
                    source_file = os.path.join(source_label_dir, img_file)
                    
                    if os.path.exists(source_file):
                        dest_file = os.path.join(dest_label_dir, img_file)
                        shutil.copy2(source_file, dest_file)
                        copied += 1
                    else:
                        print(f"    [WARNING] Không tìm thấy file: {img_file}")
            
            print(f"  [{label}] Đã sao chép {copied} ảnh từ {len(subjects)} bệnh nhân")
            total_copied += copied
    
    print("\n" + "=" * 70)
    print("HOÀN THÀNH")
    print("=" * 70)
    print(f"Tổng số ảnh đã sao chép: {total_copied}")
    print(f"Dữ liệu đã được lưu tại: {output_dir}")
    print("=" * 70)
    
    # Hiển thị cấu trúc thư mục
    print("\nCẤU TRÚC THƯ MỤC:")
    print(f"{output_dir}/")
    for split_name in ['train', 'validation', 'test']:
        split_dir = os.path.join(output_dir, split_name)
        if os.path.exists(split_dir):
            print(f"├── {split_name}/")
            for label in labels:
                label_dir = os.path.join(split_dir, label)
                if os.path.exists(label_dir):
                    n_files = len([f for f in os.listdir(label_dir) if f.endswith('.png')])
                    print(f"│   ├── {label}/ ({n_files} ảnh)")
    
    # Kiểm tra không có subject nào bị trùng lặp giữa các tập
    print("\n" + "=" * 70)
    print("KIỂM TRA TÍNH TOÀN VẸN")
    print("=" * 70)
    
    all_splits_subjects = {
        'train': set(),
        'validation': set(),
        'test': set()
    }
    
    for split_name in ['train', 'validation', 'test']:
        for label in labels:
            if label in splits[split_name]:
                all_splits_subjects[split_name].update(splits[split_name][label])
    
    # Kiểm tra overlap
    train_val_overlap = all_splits_subjects['train'] & all_splits_subjects['validation']
    train_test_overlap = all_splits_subjects['train'] & all_splits_subjects['test']
    val_test_overlap = all_splits_subjects['validation'] & all_splits_subjects['test']
    
    if len(train_val_overlap) == 0 and len(train_test_overlap) == 0 and len(val_test_overlap) == 0:
        print("✓ PASSED: Không có bệnh nhân nào bị trùng lặp giữa các tập!")
        print(f"  - Train: {len(all_splits_subjects['train'])} bệnh nhân")
        print(f"  - Validation: {len(all_splits_subjects['validation'])} bệnh nhân")
        print(f"  - Test: {len(all_splits_subjects['test'])} bệnh nhân")
        
        # Hiển thị vài ví dụ subjects trong mỗi tập
        print("\nVí dụ subjects trong mỗi tập:")
        for split_name in ['train', 'validation', 'test']:
            sample_subjects = list(all_splits_subjects[split_name])[:3]
            if sample_subjects:
                print(f"  {split_name.capitalize()}: {', '.join(sample_subjects)}{'...' if len(all_splits_subjects[split_name]) > 3 else ''}")
    else:
        print("✗ FAILED: Phát hiện bệnh nhân bị trùng lặp!")
        if len(train_val_overlap) > 0:
            print(f"  - Train & Validation overlap: {len(train_val_overlap)} bệnh nhân")
        if len(train_test_overlap) > 0:
            print(f"  - Train & Test overlap: {len(train_test_overlap)} bệnh nhân")
        if len(val_test_overlap) > 0:
            print(f"  - Validation & Test overlap: {len(val_test_overlap)} bệnh nhân")
    
    print("=" * 70)


if __name__ == "__main__":
    # Cấu hình đường dẫn
    SOURCE_DIR = r"D:\KhoaLuanTotNghiep\code\dataset_labeled"
    OUTPUT_DIR = r"D:\KhoaLuanTotNghiep\code\dataset_split"
    
    # Tỷ lệ chia (tổng phải bằng 1.0)
    TRAIN_RATIO = 0.70   # 70%
    VAL_RATIO = 0.15     # 15%
    TEST_RATIO = 0.15    # 15%
    
    # Random seed để đảm bảo reproducibility
    RANDOM_SEED = 42
    
    try:
        split_dataset_by_subject(
            source_dir=SOURCE_DIR,
            output_dir=OUTPUT_DIR,
            train_ratio=TRAIN_RATIO,
            val_ratio=VAL_RATIO,
            test_ratio=TEST_RATIO,
            random_seed=RANDOM_SEED
        )
    except Exception as e:
        print(f"\n✗ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()

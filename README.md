# Hệ Thống Xử Lý Ảnh ADNI

Dự án này xử lý dữ liệu hình ảnh não từ bộ dữ liệu ADNI (Alzheimer's Disease Neuroimaging Initiative) để phục vụ cho nghiên cứu và phân loại bệnh Alzheimer.

## Mô tả

Hệ thống bao gồm các công cụ để:

- Loại bỏ sọ não (skull stripping) từ ảnh MRI
- Chuyển đổi dữ liệu 3D sang 2D
- Gán nhãn dữ liệu dựa trên chẩn đoán
- Giao diện đồ họa (GUI) để quản lý toàn bộ quy trình

## Cấu trúc dự án

```
code/
├── skull stripping.py      # Loại bỏ sọ não từ ảnh MRI
├── make_2d_dataset.py      # Chuyển đổi ảnh 3D sang 2D
├── assign_labels.py        # Gán nhãn cho dữ liệu
├── gui_process.py          # Giao diện đồ họa
├── skull_stripped/         # Thư mục chứa ảnh đã loại sọ
├── dataset_2d/             # Thư mục chứa dữ liệu 2D
└── dataset_labeled/        # Thư mục chứa dữ liệu đã gán nhãn
```

## Yêu cầu hệ thống

- Python 3.7 trở lên
- FSL (FMRIB Software Library) để thực hiện skull stripping
- Các thư viện Python (xem file requirements.txt)

## Cài đặt

1. Clone hoặc tải dự án về máy

2. Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

3. Cài đặt FSL (cho skull stripping):
   - Tải FSL từ: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation
   - Làm theo hướng dẫn cài đặt cho hệ điều hành của bạn

## Sử dụng

### Phương pháp 1: Sử dụng GUI (Khuyến nghị)

Chạy giao diện đồ họa:

```bash
python gui_process.py
```

Trong giao diện, bạn có thể:

- Cấu hình đường dẫn thư mục
- Chạy từng bước xử lý hoặc chạy toàn bộ pipeline
- Theo dõi tiến trình xử lý real-time
- Dừng quá trình bất kỳ lúc nào

### Phương pháp 2: Chạy từng bước

#### Bước 1: Loại bỏ sọ não

```bash
python "skull stripping.py"
```

#### Bước 2: Chuyển đổi sang 2D

```bash
python make_2d_dataset.py
```

#### Bước 3: Gán nhãn

```bash
python assign_labels.py
```

## Cấu hình

Trước khi chạy, cần chỉnh sửa các đường dẫn trong từng file Python hoặc sử dụng GUI:

- `RAW_ADNI_DIR`: Thư mục chứa dữ liệu ADNI gốc
- `OUT_DIR`: Thư mục đầu ra cho từng bước
- `CSV_PATH`: Đường dẫn đến file CSV chứa thông tin chẩn đoán

## Dữ liệu đầu vào

- Ảnh MRI não định dạng NIfTI (.nii hoặc .nii.gz)
- File CSV chứa thông tin chẩn đoán (ADNIMERGE) với các cột:
  - `PTID`: Mã bệnh nhân
  - `DX`: Chẩn đoán (CN, MCI, AD, etc.)

## Dữ liệu đầu ra

- **skull_stripped/**: Ảnh MRI đã loại bỏ sọ (định dạng .nii.gz)
- **dataset_2d/**: Ảnh 2D đã được chuẩn hóa (định dạng .png)
- **dataset_labeled/**: Ảnh được tổ chức theo nhãn chẩn đoán

## Lưu ý

- Quá trình skull stripping yêu cầu FSL được cài đặt và có trong PATH
- Xử lý dữ liệu có thể mất nhiều thời gian tùy thuộc vào số lượng ảnh
- Đảm bảo có đủ dung lượng ổ đĩa cho dữ liệu đầu ra

## License

Dự án này được sử dụng cho mục đích học tập và nghiên cứu.

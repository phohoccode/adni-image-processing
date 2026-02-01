import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import os
import sys

RAW_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\test\ADNI"
SKULL_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\test\skull_stripped"
DATASET_2D_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\test\dataset_2d"
LABELED_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\test\dataset_labeled"
SPLIT_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\test\dataset_split"
CSV_PATH_DEFAULT = r"D:\KhoaLuanTotNghiep\ADNIMERGE_30Jan2026.csv"


class ADNIProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bộ Xử Lý Ảnh ADNI")
        self.root.geometry("800x800")
        
        # Xử lý khi đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variables
        self.raw_dir = tk.StringVar(value=RAW_DIR_DEFAULT)
        self.skull_dir = tk.StringVar(value=SKULL_DIR_DEFAULT)
        self.dataset_2d_dir = tk.StringVar(value=DATASET_2D_DIR_DEFAULT)
        self.labeled_dir = tk.StringVar(value=LABELED_DIR_DEFAULT)
        self.split_dir = tk.StringVar(value=SPLIT_DIR_DEFAULT)
        self.csv_path = tk.StringVar(value=CSV_PATH_DEFAULT)
        self.max_folders = tk.StringVar(value="")
        self.train_ratio = tk.StringVar(value="0.70")
        self.val_ratio = tk.StringVar(value="0.15")
        self.test_ratio = tk.StringVar(value="0.15")
        self.random_seed = tk.StringVar(value="42")
        
        self.is_running = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header = tk.Label(self.root, text="Hệ Thống Xử Lý Ảnh ADNI", 
                         font=("Arial", 16, "bold"), bg="#4CAF50", fg="white", pady=10)
        header.pack(fill="x")
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Cấu hình đường dẫn", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        configs = [
            ("ADNI Gốc:", self.raw_dir),
            ("Đã Loại Sọ:", self.skull_dir),
            ("Dữ Liệu 2D:", self.dataset_2d_dir),
            ("Dữ Liệu Đã Gán Nhãn:", self.labeled_dir),
            ("Dữ Liệu Đã Chia:", self.split_dir),
            ("File CSV:", self.csv_path),
        ]
        
        for i, (label, var) in enumerate(configs):
            tk.Label(config_frame, text=label, width=15, anchor="w").grid(row=i, column=0, sticky="w", pady=2)
            tk.Entry(config_frame, textvariable=var, width=60).grid(row=i, column=1, padx=5, pady=2)
            tk.Button(config_frame, text="...", width=3, 
                     command=lambda v=var: self.browse_path(v)).grid(row=i, column=2, pady=2)
        
        # Options Frame
        opt_frame = ttk.LabelFrame(self.root, text="Tùy chọn", padding=10)
        opt_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(opt_frame, text="Số folder xử lý (để trống = tất cả):").grid(row=0, column=0, sticky="w")
        tk.Entry(opt_frame, textvariable=self.max_folders, width=10).grid(row=0, column=1, padx=5)
        
        # Split ratios
        tk.Label(opt_frame, text="Tỷ lệ Train:").grid(row=1, column=0, sticky="w", pady=2)
        tk.Entry(opt_frame, textvariable=self.train_ratio, width=10).grid(row=1, column=1, padx=5, sticky="w")
        
        tk.Label(opt_frame, text="Tỷ lệ Validation:").grid(row=2, column=0, sticky="w", pady=2)
        tk.Entry(opt_frame, textvariable=self.val_ratio, width=10).grid(row=2, column=1, padx=5, sticky="w")
        
        tk.Label(opt_frame, text="Tỷ lệ Test:").grid(row=3, column=0, sticky="w", pady=2)
        tk.Entry(opt_frame, textvariable=self.test_ratio, width=10).grid(row=3, column=1, padx=5, sticky="w")
        
        tk.Label(opt_frame, text="Random Seed:").grid(row=4, column=0, sticky="w", pady=2)
        tk.Entry(opt_frame, textvariable=self.random_seed, width=10).grid(row=4, column=1, padx=5, sticky="w")
        
        # Main Content Frame - chia làm 2 cột (buttons bên trái, log bên phải)
        main_content = tk.Frame(self.root, bg="#f5f5f5")
        main_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left Panel - Buttons Frame
        btn_frame = tk.Frame(main_content, bg="#f5f5f5", width=250)
        btn_frame.pack(side="left", fill="y", padx=(0, 10))
        btn_frame.pack_propagate(False)  # Giữ width cố định
        
        # Tạo frame cho 4 nút chính xếp dọc
        tk.Label(btn_frame, text="Các Bước Xử Lý", font=("Arial", 12, "bold"), 
                bg="#f5f5f5", fg="#333").pack(pady=(0, 10))
        
        self.btn_skull = tk.Button(btn_frame, text="1. Loại Bỏ Sọ", 
                                   command=self.run_skull_stripping, bg="#2196F3", fg="white", 
                                   font=("Arial", 10, "bold"), height=2,
                                   relief="flat", cursor="hand2")
        self.btn_skull.pack(fill="x", padx=5, pady=5)
        
        self.btn_2d = tk.Button(btn_frame, text="2. Tạo Dữ Liệu 2D", 
                               command=self.run_make_2d, bg="#FF9800", fg="white", 
                               font=("Arial", 10, "bold"), height=2,
                               relief="flat", cursor="hand2")
        self.btn_2d.pack(fill="x", padx=5, pady=5)
        
        self.btn_label = tk.Button(btn_frame, text="3. Gán Nhãn", 
                                  command=self.run_assign_labels, bg="#9C27B0", fg="white", 
                                  font=("Arial", 10, "bold"), height=2,
                                  relief="flat", cursor="hand2")
        self.btn_label.pack(fill="x", padx=5, pady=5)
        
        self.btn_split = tk.Button(btn_frame, text="4. Chia Dữ Liệu", 
                                  command=self.run_split_dataset, bg="#009688", fg="white", 
                                  font=("Arial", 10, "bold"), height=2,
                                  relief="flat", cursor="hand2")
        self.btn_split.pack(fill="x", padx=5, pady=5)
        
        # Separator
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", padx=5, pady=15)
        
        # Nút chạy tất cả
        self.btn_all = tk.Button(btn_frame, text="▶ CHẠY TẤT CẢ", 
                                command=self.run_all, bg="#4CAF50", fg="white", 
                                font=("Arial", 11, "bold"), height=2,
                                relief="flat", cursor="hand2")
        self.btn_all.pack(fill="x", padx=5, pady=5)
        
        # Right Panel - Progress Frame
        prog_frame = ttk.LabelFrame(main_content, text="Tiến trình", padding=10)
        prog_frame.pack(side="left", fill="both", expand=True)
        
        # Nút Clear Log
        clear_frame = tk.Frame(prog_frame)
        clear_frame.pack(fill="x", pady=(0, 5))
        self.btn_clear_log = tk.Button(clear_frame, text="Xóa Log", 
                                       command=self.clear_log, bg="#9E9E9E", fg="white",
                                       font=("Arial", 9), width=12)
        self.btn_clear_log.pack(side="right")
        
        self.log_text = scrolledtext.ScrolledText(prog_frame, height=20, wrap=tk.WORD, 
                                                  font=("Consolas", 9), state="disabled")
        self.log_text.pack(fill="both", expand=True)
        
        self.progress = ttk.Progressbar(prog_frame, mode="indeterminate")
        self.progress.pack(fill="x", pady=5)
        
        # Status Bar
        self.status_label = tk.Label(self.root, text="Sẵn sàng", 
                                     bg="#E0E0E0", anchor="w", padx=10)
        self.status_label.pack(fill="x", side="bottom")
    
    def browse_path(self, var):
        if "csv" in var.get().lower():
            path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        else:
            path = filedialog.askdirectory()
        if path:
            var.set(path)
    
    def log(self, message):
        self.log_text.config(state="normal")  # Tạm thời cho phép edit
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")  # Khóa lại
        self.root.update()
    
    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
    
    def set_buttons_state(self, state):
        self.btn_skull.config(state=state)
        self.btn_2d.config(state=state)
        self.btn_label.config(state=state)
        self.btn_split.config(state=state)
        self.btn_all.config(state=state)
    
    def validate_inputs(self, step):
        """Kiểm tra input paths theo từng bước"""
        errors = []
        
        if step in [1, "all"]:
            # Bước 1: Loại bỏ sọ
            if not os.path.exists(self.raw_dir.get()):
                errors.append(f"Thư mục ADNI Gốc không tồn tại:\n{self.raw_dir.get()}")
            elif not os.path.isdir(self.raw_dir.get()):
                errors.append("ADNI Gốc phải là thư mục, không phải file")
        
        if step in [2]:
            # Bước 2: Tạo 2D dataset
            if not os.path.exists(self.skull_dir.get()):
                errors.append(f"Thư mục Đã Loại Sọ không tồn tại:\n{self.skull_dir.get()}\n\nVui lòng chạy Bước 1 trước!")
            elif not os.path.isdir(self.skull_dir.get()):
                errors.append("Đã Loại Sọ phải là thư mục")
        
        if step in [3]:
            # Bước 3: Gán nhãn
            if not os.path.exists(self.dataset_2d_dir.get()):
                errors.append(f"Thư mục Dữ Liệu 2D không tồn tại:\n{self.dataset_2d_dir.get()}\n\nVui lòng chạy Bước 2 trước!")
            elif not os.path.isdir(self.dataset_2d_dir.get()):
                errors.append("Dữ Liệu 2D phải là thư mục")
            
            if not os.path.exists(self.csv_path.get()):
                errors.append(f"File CSV không tồn tại:\n{self.csv_path.get()}")
            elif not os.path.isfile(self.csv_path.get()):
                errors.append("CSV phải là file, không phải thư mục")
        
        if step in [4]:
            # Bước 4: Chia dữ liệu
            if not os.path.exists(self.labeled_dir.get()):
                errors.append(f"Thư mục Dữ Liệu Đã Gán Nhãn không tồn tại:\n{self.labeled_dir.get()}\n\nVui lòng chạy Bước 3 trước!")
            elif not os.path.isdir(self.labeled_dir.get()):
                errors.append("Dữ Liệu Đã Gán Nhãn phải là thư mục")
            
            # Kiểm tra tỷ lệ
            try:
                train = float(self.train_ratio.get())
                val = float(self.val_ratio.get())
                test = float(self.test_ratio.get())
                
                if train <= 0 or val < 0 or test < 0:
                    errors.append("Tỷ lệ phải là số dương (train > 0, val/test >= 0)")
                
                if abs(train + val + test - 1.0) > 0.001:
                    errors.append(f"Tổng tỷ lệ phải bằng 1.0 (hiện tại: {train + val + test:.3f})")
            except ValueError:
                errors.append("Tỷ lệ train/val/test phải là số")
            
            # Kiểm tra random seed
            try:
                seed = int(self.random_seed.get())
                if seed < 0:
                    errors.append("Random seed phải >= 0")
            except ValueError:
                errors.append("Random seed phải là số nguyên")
        
        if step == "all":
            # Chạy tất cả: kiểm tra CSV luôn
            if not os.path.exists(self.csv_path.get()):
                errors.append(f"File CSV không tồn tại:\n{self.csv_path.get()}")
            elif not os.path.isfile(self.csv_path.get()):
                errors.append("CSV phải là file, không phải thư mục")
        
        # Kiểm tra max_folders nếu có
        if self.max_folders.get().strip():
            try:
                val = int(self.max_folders.get())
                if val <= 0:
                    errors.append("Số folder xử lý phải > 0")
            except ValueError:
                errors.append("Số folder xử lý phải là số nguyên")
        
        if errors:
            messagebox.showerror("Lỗi Đầu Vào", "\n\n".join(errors))
            return False
        return True
    
    def on_closing(self):
        """Xử lý khi đóng cửa sổ"""
        if self.is_running:
            response = messagebox.askyesno(
                "Xác nhận thoát", 
                "Đang có tiến trình chạy!\n\nBạn có chắc muốn thoát không?"
            )
            if response:
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run_skull_stripping(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(1):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.config(mode="determinate", value=0)
            self.status_label.config(text="Đang loại bỏ sọ...")
        
        def task():
            self.log("=" * 60)
            self.log("[BƯỚC 1] BẮT ĐẦU LOẠI BỎ SỌ")
            self.log("=" * 60)
            
            try:
                # Import hàm xử lý từ module skull stripping
                import sys
                sys.path.insert(0, os.path.dirname(__file__))
                from importlib import import_module
                skull_module = import_module('skull stripping')
                find_nii = skull_module.find_nii
                
                os.makedirs(self.skull_dir.get(), exist_ok=True)
                
                max_f = None
                if self.max_folders.get().strip():
                    max_f = int(self.max_folders.get())
                
                # Đếm tổng số folder cần xử lý
                all_folders = [s for s in os.listdir(self.raw_dir.get()) 
                              if os.path.isdir(os.path.join(self.raw_dir.get(), s))]
                total = min(len(all_folders), max_f) if max_f else len(all_folders)
                
                processed = 0
                skipped = 0
                current = 0
                for subj in all_folders:
                    current += 1
                    progress_pct = int((current / total) * 100)
                    self.progress['value'] = progress_pct
                    self.status_label.config(text=f"Loại bỏ sọ... {current}/{total} ({progress_pct}%)")
                    self.root.update()
                    
                    subj_dir = os.path.join(self.raw_dir.get(), subj)
                    if not os.path.isdir(subj_dir):
                        continue
                    
                    # Kiểm tra cả .nii.gz và .nii
                    out_file_gz = os.path.join(self.skull_dir.get(), f"{subj}_brain.nii.gz")
                    out_file_nii = os.path.join(self.skull_dir.get(), f"{subj}_brain.nii")
                    
                    # Check file existence
                    exists_gz = os.path.exists(out_file_gz)
                    exists_nii = os.path.exists(out_file_nii)
                    
                    if exists_gz or exists_nii:
                        existing_file = out_file_gz if exists_gz else out_file_nii
                        file_size = os.path.getsize(existing_file)
                        
                        # Kiểm tra file có hợp lệ không (size > 50KB)
                        if file_size > 50 * 1024:
                            self.log(f"[SKIP] Đã tồn tại: {subj} ({file_size/1024:.1f}KB)")
                            skipped += 1
                            continue
                        else:
                            # File quá nhỏ, có thể corrupt, xóa và xử lý lại
                            self.log(f"[WARNING] File cũ có vấn đề ({file_size/1024:.1f}KB), xóa và xử lý lại: {subj}")
                            os.remove(existing_file)
                    
                    # Output sẽ là .nii.gz
                    out_file = out_file_gz
                    
                    # Sử dụng hàm find_nii từ module
                    nii_path = find_nii(subj_dir)
                    if nii_path is None:
                        self.log(f"[SKIP] Không tìm thấy NII: {subj}")
                        continue
                    
                    self.log(f"[STRIP] {subj}")
                    
                    # Gọi hd-bet
                    result = subprocess.run(
                        ["hd-bet", "-i", nii_path, "-o", out_file, "-device", "cuda"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    
                    if result.returncode != 0:
                        self.log(f"[ERROR] {stderr}")
                    else:
                        processed += 1
                    
                    if max_f and processed >= max_f:
                        self.log(f"\n[DONE] Đã xử lý {processed} folders (giới hạn: {max_f})")
                        break
                
                self.log(f"\n✓ Hoàn thành loại bỏ sọ!")
                self.log(f"   - Đã xử lý: {processed} files")
                self.log(f"   - Bỏ qua: {skipped} files (đã tồn tại)")
                if standalone:
                    messagebox.showinfo("Thành công", f"Loại bỏ sọ hoàn tất!\nĐã xử lý: {processed} files\nBỏ qua: {skipped} files")
                
            except Exception as e:
                self.log(f"\n✗ LỖI: {str(e)}")
                if standalone:
                    messagebox.showerror("Lỗi", str(e))
            finally:
                if standalone:
                    self.progress['value'] = 0
                    self.status_label.config(text="Sẵn sàng")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_make_2d(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(2):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.start()
            self.status_label.config(text="Đang tạo dữ liệu 2D...")
        
        def task():
            self.log("=" * 60)
            self.log("[BƯỚC 2] BẮT ĐẦU TẠO 2D DATASET")
            self.log("=" * 60)
            
            try:
                # Import hàm xử lý từ module make_2d_dataset
                from make_2d_dataset import process_subject_to_2d
                
                os.makedirs(self.dataset_2d_dir.get(), exist_ok=True)
                
                OUT_SIZE = 128
                NUM_SLICES = 11  # số slice / subject (nên lẻ)
                
                processed = 0
                skipped = 0
                for f in os.listdir(self.skull_dir.get()):
                    if not f.endswith("_brain.nii.gz"):
                        continue
                    
                    subj = f.replace("_brain.nii.gz", "")
                    
                    # Check xem ảnh đã tồn tại chưa
                    subj_out = os.path.join(self.dataset_2d_dir.get(), subj)
                    img_file = os.path.join(subj_out, "000.png")
                    if os.path.exists(img_file):
                        self.log(f"[SKIP] Đã tồn tại: {subj}")
                        skipped += 1
                        continue
                    
                    # Sử dụng hàm từ module
                    brain_path = os.path.join(self.skull_dir.get(), f)
                    slice_count = process_subject_to_2d(
                        brain_path, 
                        self.dataset_2d_dir.get(), 
                        OUT_SIZE, 
                        NUM_SLICES,
                        self.log  # Truyền log callback
                    )
                    
                    processed += 1
                
                self.log(f"\n✓ Hoàn thành tạo 2D dataset!")
                self.log(f"   - Đã xử lý: {processed} images")
                self.log(f"   - Bỏ qua: {skipped} images (đã tồn tại)")
                if standalone:
                    messagebox.showinfo("Thành công", f"Tạo 2D dataset hoàn tất!\nĐã xử lý: {processed} images\nBỏ qua: {skipped} images")
                
            except Exception as e:
                self.log(f"\n✗ LỖI: {str(e)}")
                if standalone:
                    messagebox.showerror("Lỗi", str(e))
            finally:
                if standalone:
                    self.progress.stop()
                    self.status_label.config(text="Sẵn sàng")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_assign_labels(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(3):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.start()
            self.status_label.config(text="Đang gán nhãn...")
        
        def task():
            self.log("=" * 60)
            self.log("[BƯỚC 3] BẮT ĐẦU GÁN NHÃN")
            self.log("=" * 60)
            
            try:
                # Import hàm xử lý từ module assign_labels
                from assign_labels import load_label_map, assign_labels_for_subject
                
                os.makedirs(self.labeled_dir.get(), exist_ok=True)
                
                # Sử dụng hàm load_label_map từ module
                label_map = load_label_map(self.csv_path.get())
                
                processed = 0
                skipped = 0
                for subj in os.listdir(self.dataset_2d_dir.get()):
                    subj_dir = os.path.join(self.dataset_2d_dir.get(), subj)
                    if not os.path.isdir(subj_dir):
                        continue
                    
                    if subj not in label_map:
                        self.log(f"[SKIP] Không có label: {subj}")
                        continue
                    
                    label = label_map[subj]
                    
                    # Check xem subject đã được xử lý chưa (kiểm tra file đầu tiên)
                    out_label_dir = os.path.join(self.labeled_dir.get(), label)
                    first_file = os.path.join(out_label_dir, f"{subj}_000.png")
                    if os.path.exists(first_file):
                        self.log(f"[SKIP] Đã tồn tại: {subj}")
                        skipped += 1
                        continue
                    
                    # Sử dụng hàm từ module
                    slice_count = assign_labels_for_subject(
                        subj_dir, 
                        subj, 
                        label, 
                        self.labeled_dir.get(), 
                        self.log
                    )
                    
                    if slice_count > 0:
                        processed += 1
                
                self.log(f"\n✓ Hoàn thành gán nhãn!")
                self.log(f"   - Đã xử lý: {processed} images")
                self.log(f"   - Bỏ qua: {skipped} images (đã tồn tại)")
                if standalone:
                    messagebox.showinfo("Thành công", f"Gán nhãn hoàn tất!\nĐã xử lý: {processed} images\nBỏ qua: {skipped} images")
                
            except Exception as e:
                self.log(f"\n✗ LỖI: {str(e)}")
                if standalone:
                    messagebox.showerror("Lỗi", str(e))
            finally:
                if standalone:
                    self.progress.stop()
                    self.status_label.config(text="Sẵn sàng")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_split_dataset(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(4):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.start()
            self.status_label.config(text="Đang chia dữ liệu...")
        
        def task():
            self.log("=" * 60)
            self.log("[BƯỚC 4] BẮT ĐẦU CHIA DỮ LIỆU")
            self.log("=" * 60)
            
            try:
                # Import hàm từ module split_dataset
                from split_dataset import split_dataset_by_subject
                
                # Lấy các tham số
                train_r = float(self.train_ratio.get())
                val_r = float(self.val_ratio.get())
                test_r = float(self.test_ratio.get())
                seed = int(self.random_seed.get())
                
                self.log(f"Cấu hình:")
                self.log(f"  - Train: {train_r*100:.1f}%")
                self.log(f"  - Validation: {val_r*100:.1f}%")
                self.log(f"  - Test: {test_r*100:.1f}%")
                self.log(f"  - Random Seed: {seed}")
                self.log("")
                
                # Gọi hàm split với custom log function
                original_print = __builtins__.print
                __builtins__.print = self.log
                
                try:
                    split_dataset_by_subject(
                        source_dir=self.labeled_dir.get(),
                        output_dir=self.split_dir.get(),
                        train_ratio=train_r,
                        val_ratio=val_r,
                        test_ratio=test_r,
                        random_seed=seed
                    )
                finally:
                    __builtins__.print = original_print
                
                self.log("\n✓ Hoàn thành chia dữ liệu!")
                if standalone:
                    messagebox.showinfo("Thành công", "Chia dữ liệu hoàn tất!")
                
            except Exception as e:
                self.log(f"\n✗ LỖI: {str(e)}")
                if standalone:
                    messagebox.showerror("Lỗi", str(e))
            finally:
                if standalone:
                    self.progress.stop()
                    self.status_label.config(text="Sẵn sàng")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_all(self):
        if self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        # Validate inputs
        if not self.validate_inputs("all"):
            return
        
        response = messagebox.askyesno("Xác nhận", 
                                       "Chạy toàn bộ quy trình?\n\n" +
                                       "1. Loại Bỏ Sọ\n" +
                                       "2. Tạo Dữ Liệu 2D\n" +
                                       "3. Gán Nhãn\n" +
                                       "4. Chia Dữ Liệu")
        if not response:
            return
        
        self.is_running = True
        self.set_buttons_state(tk.DISABLED)
        self.progress.config(mode="indeterminate")
        self.progress.start()
        
        def task():
            self.log("\n" + "=" * 60)
            self.log("BẮT ĐẦU QUY TRÌNH HOÀN CHỈNH")
            self.log("=" * 60 + "\n")
            
            try:
                # Step 1
                self.status_label.config(text="Bước 1/4: Loại Bỏ Sọ...")
                self.run_skull_stripping(standalone=False)
                
                # Step 2
                self.status_label.config(text="Bước 2/4: Tạo Dữ Liệu 2D...")
                self.run_make_2d(standalone=False)
                
                # Step 3
                self.status_label.config(text="Bước 3/4: Gán Nhãn...")
                self.run_assign_labels(standalone=False)
                
                # Step 4
                self.status_label.config(text="Bước 4/4: Chia Dữ Liệu...")
                self.run_split_dataset(standalone=False)
                
                self.log("\n" + "=" * 60)
                self.log("✓ HOÀN THÀNH TOÀN BỘ QUY TRÌNH!")
                self.log("=" * 60)
                
                messagebox.showinfo("Hoàn thành", "Toàn bộ quy trình đã chạy xong!")
                
            finally:
                self.progress.stop()
                self.status_label.config(text="Sẵn sàng")
                self.is_running = False
                self.set_buttons_state(tk.NORMAL)
        
        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ADNIProcessorGUI(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\n[DỪNG] Đã dừng chương trình.")
    except Exception as e:
        print(f"\n[LỖI] {str(e)}")

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import os
import sys


class ADNIProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bộ Xử Lý Ảnh ADNI")
        self.root.geometry("800x800")
        
        # Variables
        self.raw_dir = tk.StringVar(value=r"D:\KhoaLuanTotNghiep\test\ADNI")
        self.skull_dir = tk.StringVar(value=r"D:\KhoaLuanTotNghiep\test\skull_stripped")
        self.dataset_2d_dir = tk.StringVar(value=r"D:\KhoaLuanTotNghiep\test\dataset_2d")
        self.labeled_dir = tk.StringVar(value=r"D:\KhoaLuanTotNghiep\test\dataset_labeled")
        self.csv_path = tk.StringVar(value=r"D:\KhoaLuanTotNghiep\ADNIMERGE_30Jan2026.csv")
        self.max_folders = tk.StringVar(value="")
        
        self.is_running = False
        self.stop_flag = False
        self.current_process = None  # Lưu subprocess đang chạy
        self.current_output_file = None  # Lưu file output đang xử lý
        
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
        
        # Buttons Frame
        btn_frame = tk.Frame(self.root, pady=15, bg="#f5f5f5")
        btn_frame.pack(fill="x", padx=10)
        
        # Tạo frame cho 3 nút chính
        main_btns = tk.Frame(btn_frame, bg="#f5f5f5")
        main_btns.pack(pady=5)
        
        self.btn_skull = tk.Button(main_btns, text="1. Loại Bỏ Sọ", 
                                   command=self.run_skull_stripping, bg="#2196F3", fg="white", 
                                   font=("Arial", 11, "bold"), height=2, width=20,
                                   relief="flat", cursor="hand2")
        self.btn_skull.pack(side="left", padx=8)
        
        self.btn_2d = tk.Button(main_btns, text="2. Tạo Dữ Liệu 2D", 
                               command=self.run_make_2d, bg="#FF9800", fg="white", 
                               font=("Arial", 11, "bold"), height=2, width=20,
                               relief="flat", cursor="hand2")
        self.btn_2d.pack(side="left", padx=8)
        
        self.btn_label = tk.Button(main_btns, text="3. Gán Nhãn", 
                                  command=self.run_assign_labels, bg="#9C27B0", fg="white", 
                                  font=("Arial", 11, "bold"), height=2, width=20,
                                  relief="flat", cursor="hand2")
        self.btn_label.pack(side="left", padx=8)
        
        # Nút chạy tất cả
        self.btn_all = tk.Button(btn_frame, text="▶ CHẠY TẤT CẢ", 
                                command=self.run_all, bg="#4CAF50", fg="white", 
                                font=("Arial", 13, "bold"), height=2, width=25,
                                relief="flat", cursor="hand2")
        self.btn_all.pack(pady=12)
        
        # Nút Dừng (ẩn mặc định)
        self.btn_stop = tk.Button(btn_frame, text="⏹ Dừng", 
                                 command=self.stop_process, bg="#F44336", fg="white", 
                                 font=("Arial", 10, "bold"), height=1, width=15,
                                 relief="flat", cursor="hand2")
        self.btn_stop.pack(pady=5)
        self.btn_stop.pack_forget()  # Ẩn ban đầu
        
        # Progress Frame
        prog_frame = ttk.LabelFrame(self.root, text="Tiến trình", padding=10)
        prog_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Nút Clear Log
        clear_frame = tk.Frame(prog_frame)
        clear_frame.pack(fill="x", pady=(0, 5))
        self.btn_clear_log = tk.Button(clear_frame, text="Xóa Log", 
                                       command=self.clear_log, bg="#9E9E9E", fg="white",
                                       font=("Arial", 9), width=12)
        self.btn_clear_log.pack(side="right")
        
        self.log_text = scrolledtext.ScrolledText(prog_frame, height=15, wrap=tk.WORD, 
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
        self.btn_all.config(state=state)
    
    def stop_process(self):
        self.stop_flag = True
        self.log("\n[DỪNG] Đang dừng tiến trình...")
        self.btn_stop.config(state=tk.DISABLED, text="Đang dừng...")        
        # Terminate subprocess đang chạy (nếu có)
        if self.current_process:
            try:
                self.current_process.terminate()
                self.log("[DỪNG] Đã dừng lệnh đang chạy")
            except:
                pass            
        # Xóa file corrupt (nếu có)
        if self.current_output_file and os.path.exists(self.current_output_file):
            try:
                os.remove(self.current_output_file)
                self.log(f"[DỮNG] Đã xóa file chưa hoàn thành: {os.path.basename(self.current_output_file)}")
            except:
                pass
            self.current_output_file = None
    
    def run_skull_stripping(self):
        if self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        self.is_running = True
        self.stop_flag = False
        self.set_buttons_state(tk.DISABLED)
        self.btn_stop.pack(pady=5)  # Hiển thị nút Dừng
        self.btn_stop.config(state=tk.NORMAL, text="⏹ Dừng")
        self.progress.config(mode="determinate", value=0)
        self.status_label.config(text="Đang loại bỏ sọ...")
        
        def task():
            self.log("=" * 60)
            self.log("[BƯỚC 1] BẮT ĐẦU LOẠI BỎ SỌ")
            self.log("=" * 60)
            
            try:
                import nibabel as nib
                import numpy as np
                
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
                    # Check stop flag
                    if self.stop_flag:
                        self.log(f"\n[DỪNG] Đã dừng tại {current}/{total} folders")
                        break
                    
                    current += 1
                    progress_pct = int((current / total) * 100)
                    self.progress['value'] = progress_pct
                    self.status_label.config(text=f"Loại bỏ sọ... {current}/{total} ({progress_pct}%)")
                    self.root.update()
                    
                    subj_dir = os.path.join(self.raw_dir.get(), subj)
                    if not os.path.isdir(subj_dir):
                        continue
                    
                    out_file = os.path.join(self.skull_dir.get(), f"{subj}_brain.nii.gz")
                    if os.path.exists(out_file):
                        # Kiểm tra file có hợp lệ không (size > 1MB)
                        if os.path.getsize(out_file) > 1024 * 1024:
                            self.log(f"[SKIP] Đã tồn tại: {subj}")
                            skipped += 1
                            continue
                        else:
                            # File quá nhỏ, có thể corrupt, xóa và xử lý lại
                            self.log(f"[WARNING] File cũ có vấn đề, xóa và xử lý lại: {subj}")
                            os.remove(out_file)
                    
                    nii_path = self.find_nii(subj_dir)
                    if nii_path is None:
                        self.log(f"[SKIP] Không tìm thấy NII: {subj}")
                        continue
                    
                    self.log(f"[STRIP] {subj}")
                    
                    self.current_output_file = out_file  # Lưu file đang xử lý
                    self.current_process = subprocess.Popen(
                        ["hd-bet", "-i", nii_path, "-o", out_file, "-device", "cuda"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    stdout, stderr = self.current_process.communicate()
                    returncode = self.current_process.returncode
                    self.current_process = None
                    self.current_output_file = None  # Reset sau khi xong
                    
                    if returncode != 0:
                        self.log(f"[ERROR] {stderr}")
                    
                    processed += 1
                    if max_f and processed >= max_f:
                        self.log(f"\n[DONE] Đã xử lý {processed} folders (giới hạn: {max_f})")
                        break
                
                self.log(f"\n✓ Hoàn thành loại bỏ sọ!")
                self.log(f"   - Đã xử lý: {processed} files")
                self.log(f"   - Bỏ qua: {skipped} files (đã tồn tại)")
                messagebox.showinfo("Thành công", f"Loại bỏ sọ hoàn tất!\nĐã xử lý: {processed} files\nBỏ qua: {skipped} files")
                
            except Exception as e:
                self.log(f"\n✗ LỖI: {str(e)}")
                messagebox.showerror("Lỗi", str(e))
            finally:
                self.progress['value'] = 0
                self.btn_stop.pack_forget()  # Ẩn nút Dừng
                self.btn_stop.config(state=tk.NORMAL, text="⏹ Dừng")  # Reset trạng thái
                self.current_process = None
                self.current_output_file = None
                self.status_label.config(text="Sẵn sàng")
                self.is_running = False
                self.stop_flag = False
                self.set_buttons_state(tk.NORMAL)
        
        threading.Thread(target=task, daemon=True).start()
    
    def find_nii(self, subject_dir):
        for root, _, files in os.walk(subject_dir):
            for f in files:
                if f.endswith(".nii") or f.endswith(".nii.gz"):
                    return os.path.join(root, f)
        return None
    
    def run_make_2d(self):
        if self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        self.is_running = True
        self.set_buttons_state(tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="Đang tạo dữ liệu 2D...")
        
        def task():
            self.log("=" * 60)
            self.log("[BƯỚC 2] BẮT ĐẦU TẠO 2D DATASET")
            self.log("=" * 60)
            
            try:
                import nibabel as nib
                import numpy as np
                import cv2
                import imageio
                
                os.makedirs(self.dataset_2d_dir.get(), exist_ok=True)
                
                def load_and_norm(path):
                    vol = nib.load(path)
                    vol = nib.as_closest_canonical(vol).get_fdata()
                    brain = vol[vol > 0]
                    p2, p98 = np.percentile(brain, (2, 98))
                    vol = np.clip(vol, p2, p98)
                    return (vol - p2) / (p98 - p2 + 1e-8)
                
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
                    
                    self.log(f"[2D] {subj}")
                    
                    vol = load_and_norm(os.path.join(self.skull_dir.get(), f))
                    
                    areas = [np.count_nonzero(vol[:, i, :]) for i in range(vol.shape[1])]
                    best = np.argmax(areas)
                    
                    img = vol[:, best, :]
                    img = np.rot90(img, k=1)
                    img = cv2.resize(img, (128, 128))
                    img = (img * 255).astype(np.uint8)
                    
                    os.makedirs(subj_out, exist_ok=True)
                    imageio.imwrite(img_file, img)
                    processed += 1
                
                self.log(f"\n✓ Hoàn thành tạo 2D dataset!")
                self.log(f"   - Đã xử lý: {processed} images")
                self.log(f"   - Bỏ qua: {skipped} images (đã tồn tại)")
                messagebox.showinfo("Thành công", f"Tạo 2D dataset hoàn tất!\nĐã xử lý: {processed} images\nBỏ qua: {skipped} images")
                
            except Exception as e:
                self.log(f"\n✗ LỖI: {str(e)}")
                messagebox.showerror("Lỗi", str(e))
            finally:
                self.progress.stop()
                self.status_label.config(text="Sẵn sàng")
                self.is_running = False
                self.set_buttons_state(tk.NORMAL)
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_assign_labels(self):
        if self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        self.is_running = True
        self.set_buttons_state(tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="Đang gán nhãn...")
        
        def task():
            self.log("=" * 60)
            self.log("[BƯỚC 3] BẮT ĐẦU GÁN NHÃN")
            self.log("=" * 60)
            
            try:
                import pandas as pd
                import shutil
                
                os.makedirs(self.labeled_dir.get(), exist_ok=True)
                
                df = pd.read_csv(self.csv_path.get())
                df = df[["PTID", "DX"]].dropna()
                df = df.drop_duplicates("PTID")
                label_map = dict(zip(df.PTID, df.DX))
                
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
                    out_label_dir = os.path.join(self.labeled_dir.get(), label)
                    os.makedirs(out_label_dir, exist_ok=True)
                    
                    img_src = os.path.join(subj_dir, "000.png")
                    img_dst = os.path.join(out_label_dir, f"{subj}.png")
                    
                    # Check xem ảnh đã được gán label chưa
                    if os.path.exists(img_dst):
                        self.log(f"[SKIP] Đã tồn tại: {subj}")
                        skipped += 1
                        continue
                    
                    if os.path.exists(img_src):
                        shutil.copy2(img_src, img_dst)
                        self.log(f"[LABEL] {subj} → {label}")
                        processed += 1
                
                self.log(f"\n✓ Hoàn thành gán nhãn!")
                self.log(f"   - Đã xử lý: {processed} images")
                self.log(f"   - Bỏ qua: {skipped} images (đã tồn tại)")
                messagebox.showinfo("Thành công", f"Gán nhãn hoàn tất!\nĐã xử lý: {processed} images\nBỏ qua: {skipped} images")
                
            except Exception as e:
                self.log(f"\n✗ LỖI: {str(e)}")
                messagebox.showerror("Lỗi", str(e))
            finally:
                self.progress.stop()
                self.status_label.config(text="Sẵn sàng")
                self.is_running = False
                self.set_buttons_state(tk.NORMAL)
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_all(self):
        if self.is_running:
            messagebox.showwarning("Cảnh báo", "Đang có tiến trình chạy!")
            return
        
        response = messagebox.askyesno("Xác nhận", 
                                       "Chạy toàn bộ quy trình?\n\n" +
                                       "1. Loại Bỏ Sọ\n" +
                                       "2. Tạo Dữ Liệu 2D\n" +
                                       "3. Gán Nhãn")
        if not response:
            return
        
        self.is_running = True
        self.stop_flag = False
        self.set_buttons_state(tk.DISABLED)
        self.btn_stop.pack(pady=5)  # Hiển thị nút Dừng
        self.btn_stop.config(state=tk.NORMAL, text="⏹ Dừng")
        self.progress.config(mode="indeterminate")
        self.progress.start()
        
        def task():
            self.log("\n" + "=" * 60)
            self.log("BẮT ĐẦU QUY TRÌNH HOÀN CHỈNH")
            self.log("=" * 60 + "\n")
            
            # Step 1
            self.status_label.config(text="Bước 1/3: Loại Bỏ Sọ...")
            self.run_step_1()
            
            # Step 2
            self.status_label.config(text="Bước 2/3: Tạo Dữ Liệu 2D...")
            self.run_step_2()
            
            # Step 3
            self.status_label.config(text="Bước 3/3: Gán Nhãn...")
            self.run_step_3()
            
            self.log("\n" + "=" * 60)
            self.log("✓ HOÀN THÀNH TOÀN BỘ QUY TRÌNH!")
            self.log("=" * 60)
            
            messagebox.showinfo("Hoàn thành", "Toàn bộ quy trình đã chạy xong!")
            
            self.progress.stop()
            self.btn_stop.pack_forget()  # Ẩn nút Dừng
            self.btn_stop.config(state=tk.NORMAL, text="⏹ Dừng")  # Reset trạng thái
            self.current_process = None
            self.current_output_file = None
            self.status_label.config(text="Sẵn sàng")
            self.is_running = False
            self.stop_flag = False
            self.set_buttons_state(tk.NORMAL)
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_step_1(self):
        # Inline skull stripping
        self.log("[BƯỚC 1] Loại Bỏ Sọ...")
        try:
            os.makedirs(self.skull_dir.get(), exist_ok=True)
            max_f = None
            if self.max_folders.get().strip():
                max_f = int(self.max_folders.get())
            
            processed = 0
            skipped = 0
            for subj in os.listdir(self.raw_dir.get()):
                if self.stop_flag:
                    self.log("  [DỮNG] Đã dừng loại bỏ sọ")
                    break
                
                subj_dir = os.path.join(self.raw_dir.get(), subj)
                if not os.path.isdir(subj_dir):
                    continue
                
                out_file = os.path.join(self.skull_dir.get(), f"{subj}_brain.nii.gz")
                if os.path.exists(out_file):
                    if os.path.getsize(out_file) > 1024 * 1024:
                        self.log(f"  [SKIP] Đã tồn tại: {subj}")
                        skipped += 1
                        continue
                    else:
                        self.log(f"  [WARNING] Xóa file cũ có vấn đề: {subj}")
                        os.remove(out_file)
                
                nii_path = self.find_nii(subj_dir)
                if nii_path is None:
                    continue
                
                self.log(f"  [STRIP] {subj}")
                
                self.current_output_file = out_file
                self.current_process = subprocess.Popen(
                    ["hd-bet", "-i", nii_path, "-o", out_file, "-device", "cuda"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                self.current_process.communicate()
                self.current_process = None
                self.current_output_file = None
                
                processed += 1
                
                if max_f and processed >= max_f:
                    break
            
            self.log(f"  ✓ Xong bước 1: {processed} files (bỏ qua: {skipped})\n")
        except Exception as e:
            self.log(f"  ✗ Lỗi bước 1: {e}\n")
    
    def run_step_2(self):
        # Inline make 2D
        self.log("[BƯỚC 2] Tạo Dữ Liệu 2D...")
        try:
            import nibabel as nib
            import numpy as np
            import cv2
            import imageio
            
            os.makedirs(self.dataset_2d_dir.get(), exist_ok=True)
            
            def load_and_norm(path):
                vol = nib.load(path)
                vol = nib.as_closest_canonical(vol).get_fdata()
                brain = vol[vol > 0]
                p2, p98 = np.percentile(brain, (2, 98))
                vol = np.clip(vol, p2, p98)
                return (vol - p2) / (p98 - p2 + 1e-8)
            
            processed = 0
            skipped = 0
            for f in os.listdir(self.skull_dir.get()):
                if not f.endswith("_brain.nii.gz"):
                    continue
                
                subj = f.replace("_brain.nii.gz", "")
                
                subj_out = os.path.join(self.dataset_2d_dir.get(), subj)
                img_file = os.path.join(subj_out, "000.png")
                if os.path.exists(img_file):
                    self.log(f"  [SKIP] Đã tồn tại: {subj}")
                    skipped += 1
                    continue
                
                vol = load_and_norm(os.path.join(self.skull_dir.get(), f))
                
                areas = [np.count_nonzero(vol[:, i, :]) for i in range(vol.shape[1])]
                best = np.argmax(areas)
                
                img = vol[:, best, :]
                img = np.rot90(img, k=1)
                img = cv2.resize(img, (128, 128))
                img = (img * 255).astype(np.uint8)
                
                os.makedirs(subj_out, exist_ok=True)
                imageio.imwrite(img_file, img)
                processed += 1
            
            self.log(f"  ✓ Xong bước 2: {processed} images (bỏ qua: {skipped})\n")
        except Exception as e:
            self.log(f"  ✗ Lỗi bước 2: {e}\n")
    
    def run_step_3(self):
        # Inline assign labels
        self.log("[BƯỚC 3] Gán Nhãn...")
        try:
            import pandas as pd
            import shutil
            
            os.makedirs(self.labeled_dir.get(), exist_ok=True)
            
            df = pd.read_csv(self.csv_path.get())
            df = df[["PTID", "DX"]].dropna()
            df = df.drop_duplicates("PTID")
            label_map = dict(zip(df.PTID, df.DX))
            
            processed = 0
            skipped = 0
            for subj in os.listdir(self.dataset_2d_dir.get()):
                subj_dir = os.path.join(self.dataset_2d_dir.get(), subj)
                if not os.path.isdir(subj_dir):
                    continue
                
                if subj not in label_map:
                    continue
                
                label = label_map[subj]
                out_label_dir = os.path.join(self.labeled_dir.get(), label)
                os.makedirs(out_label_dir, exist_ok=True)
                
                img_src = os.path.join(subj_dir, "000.png")
                img_dst = os.path.join(out_label_dir, f"{subj}.png")
                
                if os.path.exists(img_dst):
                    self.log(f"  [SKIP] Đã tồn tại: {subj}")
                    skipped += 1
                    continue
                
                if os.path.exists(img_src):
                    shutil.copy2(img_src, img_dst)
                    processed += 1
            
            self.log(f"  ✓ Xong bước 3: {processed} images (bỏ qua: {skipped})\n")
        except Exception as e:
            self.log(f"  ✗ Lỗi bước 3: {e}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = ADNIProcessorGUI(root)
    root.mainloop()

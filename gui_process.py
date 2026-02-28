import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import os
import sys

RAW_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\ThucNghiem\ADNI"
SKULL_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\ThucNghiem\skull_stripped"
MNI_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\ThucNghiem\mni_registered"
DATASET_2D_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\ThucNghiem\dataset_2d"
LABELED_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\ThucNghiem\dataset_labeled"
SPLIT_DIR_DEFAULT = r"D:\KhoaLuanTotNghiep\ThucNghiem\dataset_split"
CSV_PATH_DEFAULT = r"D:\KhoaLuanTotNghiep\ThucNghiem\ADNIMERGE.csv"


class ADNIProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ADNI Image Processing Suite")
        self.root.geometry("800x800")
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variables
        self.raw_dir = tk.StringVar(value=RAW_DIR_DEFAULT)
        self.skull_dir = tk.StringVar(value=SKULL_DIR_DEFAULT)
        self.mni_dir = tk.StringVar(value=MNI_DIR_DEFAULT)
        self.dataset_2d_dir = tk.StringVar(value=DATASET_2D_DIR_DEFAULT)
        self.labeled_dir = tk.StringVar(value=LABELED_DIR_DEFAULT)
        self.split_dir = tk.StringVar(value=SPLIT_DIR_DEFAULT)
        self.csv_path = tk.StringVar(value=CSV_PATH_DEFAULT)
        self.max_folders = tk.StringVar(value="")
        self.train_ratio = tk.StringVar(value="0.70")
        self.val_ratio = tk.StringVar(value="0.15")
        self.test_ratio = tk.StringVar(value="0.15")
        self.random_seed = tk.StringVar(value="42")
        
        # Label selection checkboxes
        self.label_cn = tk.BooleanVar(value=True)
        self.label_emci = tk.BooleanVar(value=True)
        self.label_lmci = tk.BooleanVar(value=True)
        self.label_smc = tk.BooleanVar(value=True)
        self.label_ad = tk.BooleanVar(value=True)
        
        self.is_running = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header = tk.Label(self.root, text="ADNI Image Processing Suite", 
                         font=("Arial", 16, "bold"), bg="#4CAF50", fg="white", pady=10)
        header.pack(fill="x")
        
        # Container frame to hold config and options horizontally
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Configuration Frame - không expand, chỉ chiếm chiều ngang vừa đủ
        config_frame = ttk.LabelFrame(top_frame, text="Path Configuration", padding=10)
        config_frame.pack(side="left", fill="y", padx=(0, 5))
        
        configs = [
            ("Raw ADNI:", self.raw_dir),
            ("Skull Stripped:", self.skull_dir),
            ("MNI Registered:", self.mni_dir),
            ("Dataset 2D:", self.dataset_2d_dir),
            ("Labeled Dataset:", self.labeled_dir),
            ("Split Dataset:", self.split_dir),
            ("File CSV:", self.csv_path),
        ]
        
        for i, (label, var) in enumerate(configs):
            tk.Label(config_frame, text=label, width=15, anchor="w").grid(row=i, column=0, sticky="w", pady=2)
            tk.Entry(config_frame, textvariable=var, width=50).grid(row=i, column=1, padx=5, pady=2)
            tk.Button(config_frame, text="...", width=3, 
                     command=lambda v=var: self.browse_path(v)).grid(row=i, column=2, pady=2)
        
        # Options Frame
        opt_frame = ttk.LabelFrame(top_frame, text="Options (Step 5 only)", padding=10)
        opt_frame.pack(side="left", fill="both", padx=(5, 0))
        
        tk.Label(opt_frame, text="Number of folders to process (leave blank = all):").grid(row=0, column=0, sticky="w")
        tk.Entry(opt_frame, textvariable=self.max_folders, width=10).grid(row=0, column=1, padx=5)
        
        # Split ratios
        tk.Label(opt_frame, text="Train Ratio:").grid(row=1, column=0, sticky="w", pady=2)
        tk.Entry(opt_frame, textvariable=self.train_ratio, width=10).grid(row=1, column=1, padx=5, sticky="w")
        
        tk.Label(opt_frame, text="Validation Ratio:").grid(row=2, column=0, sticky="w", pady=2)
        tk.Entry(opt_frame, textvariable=self.val_ratio, width=10).grid(row=2, column=1, padx=5, sticky="w")
        
        tk.Label(opt_frame, text="Test Ratio:").grid(row=3, column=0, sticky="w", pady=2)
        tk.Entry(opt_frame, textvariable=self.test_ratio, width=10).grid(row=3, column=1, padx=5, sticky="w")
        
        tk.Label(opt_frame, text="Random Seed:").grid(row=4, column=0, sticky="w", pady=2)
        tk.Entry(opt_frame, textvariable=self.random_seed, width=10).grid(row=4, column=1, padx=5, sticky="w")
        
        # Label selection section
        ttk.Separator(opt_frame, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        tk.Label(opt_frame, text="Select Labels to Process (Step 4 only):", font=("Arial", 9, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        # Arrange checkboxes in 2 columns to save vertical space
        tk.Checkbutton(opt_frame, text="CN", variable=self.label_cn).grid(row=7, column=0, sticky="w", padx=(0, 10))
        tk.Checkbutton(opt_frame, text="LMCI", variable=self.label_lmci).grid(row=7, column=1, sticky="w")
        tk.Checkbutton(opt_frame, text="EMCI", variable=self.label_emci).grid(row=8, column=0, sticky="w", padx=(0, 10))
        tk.Checkbutton(opt_frame, text="AD", variable=self.label_ad).grid(row=8, column=1, sticky="w")
        tk.Checkbutton(opt_frame, text="SMC", variable=self.label_smc).grid(row=9, column=0, sticky="w", padx=(0, 10))
        
        # Main Content Frame - split into 2 columns (buttons on the left, log on the right)
        main_content = tk.Frame(self.root, bg="#f5f5f5")
        main_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left Panel - Buttons Frame
        btn_frame = tk.Frame(main_content, bg="#f5f5f5", width=250)
        btn_frame.pack(side="left", fill="y", padx=(0, 10))
        btn_frame.pack_propagate(False)  # Keep fixed width
        
        # Create frame for 4 main buttons stacked vertically
        tk.Label(btn_frame, text="Processing Steps", font=("Arial", 12, "bold"), 
                bg="#f5f5f5", fg="#333").pack(pady=(0, 10))
        
        self.btn_skull = tk.Button(btn_frame, text="1. Skull Stripping", 
                                   command=self.run_skull_stripping, bg="#2196F3", fg="white", 
                                   font=("Arial", 10, "bold"), height=2,
                                   relief="flat", cursor="hand2")
        self.btn_skull.pack(fill="x", padx=5, pady=5)
        
        self.btn_mni = tk.Button(btn_frame, text="2. MNI Registration", 
                                command=self.run_mni_registration, bg="#E91E63", fg="white", 
                                font=("Arial", 10, "bold"), height=2,
                                relief="flat", cursor="hand2")
        self.btn_mni.pack(fill="x", padx=5, pady=5)
        
        self.btn_2d = tk.Button(btn_frame, text="3. Create 2D Dataset", 
                               command=self.run_make_2d, bg="#FF9800", fg="white", 
                               font=("Arial", 10, "bold"), height=2,
                               relief="flat", cursor="hand2")
        self.btn_2d.pack(fill="x", padx=5, pady=5)
        
        self.btn_label = tk.Button(btn_frame, text="4. Assign Labels", 
                                  command=self.run_assign_labels, bg="#9C27B0", fg="white", 
                                  font=("Arial", 10, "bold"), height=2,
                                  relief="flat", cursor="hand2")
        self.btn_label.pack(fill="x", padx=5, pady=5)
        
        self.btn_split = tk.Button(btn_frame, text="5. Split Dataset", 
                                  command=self.run_split_dataset, bg="#009688", fg="white", 
                                  font=("Arial", 10, "bold"), height=2,
                                  relief="flat", cursor="hand2")
        self.btn_split.pack(fill="x", padx=5, pady=5)
        
        # Separator
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", padx=5, pady=15)
        
        # Nút chạy tất cả
        self.btn_all = tk.Button(btn_frame, text="▶ Run All Steps", 
                                command=self.run_all, bg="#4CAF50", fg="white", 
                                font=("Arial", 11, "bold"), height=2,
                                relief="flat", cursor="hand2")
        self.btn_all.pack(fill="x", padx=5, pady=5)
        
        # Right Panel - Progress Frame
        prog_frame = ttk.LabelFrame(main_content, text="Progress", padding=10)
        prog_frame.pack(side="left", fill="both", expand=True)
        
        # Nút Clear Log
        clear_frame = tk.Frame(prog_frame)
        clear_frame.pack(fill="x", pady=(0, 5))
        self.btn_clear_log = tk.Button(clear_frame, text="Clear Log", 
                                       command=self.clear_log, bg="#9E9E9E", fg="white",
                                       font=("Arial", 9), width=12)
        self.btn_clear_log.pack(side="right")
        
        # Progress bar với label % - ĐẶT TRƯỚC LOG
        progress_container = tk.Frame(prog_frame, bg="#f0f0f0", relief="solid", borderwidth=1)
        progress_container.pack(fill="x", pady=(0, 10), padx=5)
        
        tk.Label(progress_container, text="Progress:", font=("Arial", 9, "bold"), 
                bg="#f0f0f0").pack(side="left", padx=5)
        
        self.progress = ttk.Progressbar(progress_container, mode="indeterminate", length=300)
        self.progress.pack(side="left", fill="x", expand=True, pady=8, padx=5)
        
        self.progress_label = tk.Label(progress_container, text="", width=6, 
                                       font=("Arial", 12, "bold"), fg="#2196F3", bg="#f0f0f0")
        self.progress_label.pack(side="left", padx=5)
        
        self.log_text = scrolledtext.ScrolledText(prog_frame, height=20, wrap=tk.WORD, 
                                                  font=("Consolas", 9), state="disabled")
        self.log_text.pack(fill="both", expand=True)
        
        # Status Bar
        self.status_label = tk.Label(self.root, text="Ready", 
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
        self.btn_mni.config(state=state)
        self.btn_2d.config(state=state)
        self.btn_label.config(state=state)
        self.btn_split.config(state=state)
        self.btn_all.config(state=state)
    
    def validate_inputs(self, step):
        """Validate input paths for each step"""
        errors = []
        
        if step in [1, "all"]:
            # Step 1: Skull Stripping
            if not os.path.exists(self.raw_dir.get()):
                errors.append(f"Raw ADNI directory does not exist:\n{self.raw_dir.get()}")
            elif not os.path.isdir(self.raw_dir.get()):
                errors.append("Raw ADNI must be a directory, not a file")
        
        if step in [2]:
            # Step 2: MNI Registration
            if not os.path.exists(self.skull_dir.get()):
                errors.append(f"Skull Stripped directory does not exist:\n{self.skull_dir.get()}\n\nPlease run Step 1 first!")
            elif not os.path.isdir(self.skull_dir.get()):
                errors.append("Skull Stripped must be a directory")
        
        if step in [3]:
            # Step 3: Create 2D Dataset
            if not os.path.exists(self.mni_dir.get()):
                errors.append(f"MNI Registered directory does not exist:\n{self.mni_dir.get()}\n\nPlease run Step 2 first!")
            elif not os.path.isdir(self.mni_dir.get()):
                errors.append("MNI Registered must be a directory")
        
        if step in [4]:
            # Step 4: Labeling
            if not os.path.exists(self.dataset_2d_dir.get()):
                errors.append(f"2D Dataset directory does not exist:\n{self.dataset_2d_dir.get()}\n\nPlease run Step 3 first!")
            elif not os.path.isdir(self.dataset_2d_dir.get()):
                errors.append("2D Dataset must be a directory")
            
            if not os.path.exists(self.csv_path.get()):
                errors.append(f"CSV file does not exist:\n{self.csv_path.get()}")
            elif not os.path.isfile(self.csv_path.get()):
                errors.append("CSV must be a file, not a directory")
            
            # Check if at least one label is selected
            if not any([self.label_cn.get(), self.label_emci.get(), 
                       self.label_lmci.get(), self.label_smc.get(), self.label_ad.get()]):
                errors.append("Please select at least one label to process")
            
        
        if step in [5]:
            # Step 5: Split Data
            if not os.path.exists(self.labeled_dir.get()):
                errors.append(f"Labeled Data directory does not exist:\n{self.labeled_dir.get()}\n\nPlease run Step 4 first!")
            elif not os.path.isdir(self.labeled_dir.get()):
                errors.append("Labeled Data must be a directory")
            
            # Check ratios
            try:
                train = float(self.train_ratio.get())
                val = float(self.val_ratio.get())
                test = float(self.test_ratio.get())
                
                if train <= 0 or val < 0 or test < 0:
                    errors.append("Ratios must be positive numbers (train > 0, val/test >= 0)")
                
                if abs(train + val + test - 1.0) > 0.001:
                    errors.append(f"Sum of ratios must be 1.0 (current: {train + val + test:.3f})")
            except ValueError:
                errors.append("Train/val/test ratios must be numbers")
            
            # Check random seed
            try:
                seed = int(self.random_seed.get())
                if seed < 0:
                    errors.append("Random seed must be >= 0")
            except ValueError:
                errors.append("Random seed must be an integer")
        
        if step == "all":
            # Run all: always check CSV too
            if not os.path.exists(self.csv_path.get()):
                errors.append(f"CSV file does not exist:\n{self.csv_path.get()}")
            elif not os.path.isfile(self.csv_path.get()):
                errors.append("CSV must be a file, not a directory")
        
        # Check max_folders if any
        if self.max_folders.get().strip():
            try:
                val = int(self.max_folders.get())
                if val <= 0:
                    errors.append("Number of folders to process must be > 0")
            except ValueError:
                errors.append("Number of folders to process must be an integer")
        
        if errors:
            messagebox.showerror("Input Error", "\n\n".join(errors))
            return False
        return True
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            response = messagebox.askyesno(
                "Confirm Exit", 
                "A process is currently running!\n\nAre you sure you want to exit?"
            )
            if response:
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run_skull_stripping(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Warning", "A process is currently running!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(1):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.config(mode="determinate", value=0)
            self.status_label.config(text="Running skull stripping...")
        
        def task():
            self.log("=" * 60)
            self.log("[STEP 1] STARTING SKULL STRIPPING")
            self.log("=" * 60)
            
            try:
                # Import processing function from skull stripping module
                import sys
                sys.path.insert(0, os.path.dirname(__file__)) # 
                from importlib import import_module
                skull_module = import_module('skull stripping')
                find_nii = skull_module.find_nii
                
                os.makedirs(self.skull_dir.get(), exist_ok=True)
                
                max_f = None
                if self.max_folders.get().strip():
                    max_f = int(self.max_folders.get())
                
                # Count total number of folders to process
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
                    self.progress_label.config(text=f"{progress_pct}%")
                    self.status_label.config(text=f"Skull Stripping... {current}/{total} ({progress_pct}%)")
                    self.root.update()
                    
                    subj_dir = os.path.join(self.raw_dir.get(), subj)
                    if not os.path.isdir(subj_dir):
                        continue
                    
                    # Check both .nii.gz and .nii
                    out_file_gz = os.path.join(self.skull_dir.get(), f"{subj}_brain.nii.gz")
                    out_file_nii = os.path.join(self.skull_dir.get(), f"{subj}_brain.nii")
                    
                    # Check file existence
                    exists_gz = os.path.exists(out_file_gz)
                    exists_nii = os.path.exists(out_file_nii)
                    
                    if exists_gz or exists_nii:
                        existing_file = out_file_gz if exists_gz else out_file_nii
                        file_size = os.path.getsize(existing_file)
                        
                        # Check if file is valid (size > 1MB)
                        if file_size > 1000 * 1024:
                            self.log(f"[SKIP] Already exists: {subj} ({file_size/1024:.1f}KB)")
                            skipped += 1
                            continue
                        else:
                            # File too small, possibly corrupt, delete and reprocess
                            self.log(f"[WARNING] Old file too small ({file_size/1024:.1f}KB), deleting and reprocessing: {subj}")
                            os.remove(existing_file)
                    
                    # Output will be .nii.gz
                    out_file = out_file_gz
                    
                    # Use find_nii function from module
                    nii_path = find_nii(subj_dir)
                    if nii_path is None:
                        self.log(f"[SKIP] NII not found: {subj}")
                        continue
                    
                    self.log(f"[STRIP] {subj}")
                    
                    # Call hd-bet
                    result = subprocess.run(
                        ["hd-bet", "-i", nii_path, "-o", out_file, "-device", "cuda"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    
                    if result.returncode != 0:
                        self.log(f"[ERROR] {result.stderr}")
                    else:                        # Kiểm tra kích thước file output
                        if os.path.exists(out_file):
                            file_size = os.path.getsize(out_file)
                            if file_size < 1000 * 1024:  # Nhỏ hơn 2 MB = có vấn đề
                                self.log(f"  WARNING: Output file too small ({file_size/1024:.1f} KB) - may be corrupted")
                            else:
                                self.log(f"  ✓ Success ({file_size/1024/1024:.2f} MB)")
                        processed += 1
                    
                    if max_f and processed >= max_f:
                        self.log(f"\n[DONE] Processed {processed} folders (limit: {max_f})")
                        break
                
                self.log(f"\n✓ Skull stripping completed!")
                self.log(f"   - Processed: {processed} files")
                self.log(f"   - Skipped: {skipped} files (already exist)")
                if standalone:
                    messagebox.showinfo("Success", f"Skull stripping completed!\nProcessed: {processed} files\nSkipped: {skipped} files")
                
            except Exception as e:
                self.log(f"\n✗ ERROR: {str(e)}")
                if standalone:
                    messagebox.showerror("Error", str(e))
            finally:
                if standalone:
                    self.progress['value'] = 0
                    self.progress_label.config(text="")
                    self.status_label.config(text="Ready")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_mni_registration(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Warning", "A process is already running!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(2):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.config(mode="determinate", value=0)
            self.status_label.config(text="Registering to MNI...")
        
        def task():
            self.log("=" * 60)
            self.log("[STEP 2] STARTING MNI REGISTRATION")
            self.log("=" * 60)
            
            try:
                # Import functions from mni_registration module
                from mni_registration import register_to_mni, check_fsl_installed, MNI_TEMPLATE_WSL
                
                # Kiểm tra FSL đã cài đặt
                if not check_fsl_installed():
                    self.log("[ERROR] FSL is not installed in WSL or WSL is not installed")
                    self.log("Please:")
                    self.log("  1. Install WSL: wsl --install -d Ubuntu-22.04")
                    self.log("  2. Install FSL in WSL: https://fsl.fmrib.ox.ac.uk/fsl/docs/install/linux.html")
                    if standalone:
                        messagebox.showerror("Error", "FSL is not installed in WSL")
                    return
                
                self.log(f"Using MNI template: {MNI_TEMPLATE_WSL}")
                
                os.makedirs(self.mni_dir.get(), exist_ok=True)
                
                # Lấy danh sách các file đã skull stripping (cả .nii và .nii.gz)
                brain_files = [f for f in os.listdir(self.skull_dir.get()) 
                              if f.endswith("_brain.nii.gz") or f.endswith("_brain.nii")]
                
                total = len(brain_files)
                self.log(f"Found {total} subjects to register")
                self.log("")
                
                processed = 0
                skipped = 0
                failed = 0
                
                for i, brain_file in enumerate(brain_files, 1):
                    progress_pct = int((i / total) * 100)
                    self.progress['value'] = progress_pct
                    self.progress_label.config(text=f"{progress_pct}%")
                    self.status_label.config(text=f"MNI Registration... {i}/{total} ({progress_pct}%)")
                    self.root.update()
                    
                    input_path = os.path.join(self.skull_dir.get(), brain_file)
                    subj_id = brain_file.replace("_brain.nii.gz", "").replace("_brain.nii", "")
                    output_path_gz = os.path.join(self.mni_dir.get(), f"{subj_id}_mni.nii.gz")
                    output_path_nii = os.path.join(self.mni_dir.get(), f"{subj_id}_mni.nii")
                    
                    # Bỏ qua nếu đã xử lý (check cả .nii.gz và .nii)
                    exists_gz = os.path.exists(output_path_gz)
                    exists_nii = os.path.exists(output_path_nii)
                    
                    if exists_gz or exists_nii:
                        existing_file = output_path_gz if exists_gz else output_path_nii
                        file_size = os.path.getsize(existing_file)
                        if file_size > 100 * 1024:  # > 100KB
                            self.log(f"[{i}/{total}] [SKIP] Đã tồn tại: {subj_id} ({file_size/1024:.1f}KB)")
                            skipped += 1
                            continue
                        else:
                            self.log(f"[{i}/{total}] [WARNING] Old file has issues, deleting and reprocessing: {subj_id}")
                            os.remove(existing_file)
                    
                    # Default output is .nii.gz
                    output_path = output_path_gz
                    
                    self.log(f"[{i}/{total}] [MNI] {subj_id}")
                    
                    # Perform registration
                    success = register_to_mni(input_path, output_path, MNI_TEMPLATE_WSL, self.log)
                    
                    if success:
                        processed += 1
                        self.log(f"  ✓ Success")
                    else:
                        failed += 1
                        self.log(f"  ✗ Failed")
                
                self.log(f"\n✓ MNI registration completed!")
                self.log(f"   - Processed: {processed} files")
                self.log(f"   - Skipped: {skipped} files (already exist)")
                self.log(f"   - Failed: {failed} files")
                
                if standalone:
                    messagebox.showinfo("Success", 
                                      f"MNI registration completed!\n\n" +
                                      f"Processed: {processed} files\n" +
                                      f"Skipped: {skipped} files\n" +
                                      f"Failed: {failed} files")
                
            except ImportError as e:
                self.log(f"\n✗ ERROR: Cannot import mni_registration module")
                self.log(f"Details: {str(e)}")
                if standalone:
                    messagebox.showerror("Error", "Cannot import mni_registration module!\n\nEnsure the file mni_registration.py exists in the same directory.")
            except Exception as e:
                self.log(f"\n✗ ERROR: {str(e)}")
                if standalone:
                    messagebox.showerror("Error", str(e))
            finally:
                if standalone:
                    self.progress['value'] = 0
                    self.progress_label.config(text="")
                    self.status_label.config(text="Ready")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_make_2d(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Warning", "A process is already running!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(3):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.config(mode="determinate", value=0)
            self.status_label.config(text="Creating 2D dataset...")
        
        def task():
            self.log("=" * 60)
            self.log("[STEP 3] STARTING 2D DATASET CREATION")
            self.log("=" * 60)
            
            try:
                # Import processing function from make_2d_dataset module
                from make_2d_dataset import process_subject_to_2d
                
                os.makedirs(self.dataset_2d_dir.get(), exist_ok=True)
                
                OUT_SIZE = 224
                NUM_SLICES = 11  # số slice / subject (nên lẻ)
                
                # Ưu tiên đọc từ mni_registered, fallback về skull_stripped
                source_dir = self.mni_dir.get() if os.path.exists(self.mni_dir.get()) else self.skull_dir.get()
                self.log(f"Data source: {source_dir}")
                
                # Đếm tổng số file cần xử lý
                all_files = [f for f in os.listdir(source_dir) 
                            if f.endswith("_mni.nii.gz") or f.endswith("_brain.nii.gz")]
                total = len(all_files)
                self.log(f"Total files to process: {total}")
                
                processed = 0
                skipped = 0
                
                for idx, f in enumerate(all_files, 1):
                    subj = f.replace("_mni.nii.gz", "").replace("_brain.nii.gz", "")
                    
                    # Check xem ảnh đã tồn tại chưa
                    subj_out = os.path.join(self.dataset_2d_dir.get(), subj)
                    img_file = os.path.join(subj_out, "000.png")
                    if os.path.exists(img_file):
                        self.log(f"[SKIP] Already exists: {subj}")
                        skipped += 1
                        # Update progress
                        pct = int((idx / total) * 100)
                        self.progress.config(value=pct)
                        self.progress_label.config(text=f"{pct}%")
                        continue
                    
                    # Check file size - skip if too small (< 1MB)
                    brain_path = os.path.join(source_dir, f)
                    file_size = os.path.getsize(brain_path)
                    if file_size < 1000 * 1024:  # < 1MB
                        self.log(f"[SKIP] File too small ({file_size/1024:.1f}KB): {subj}")
                        skipped += 1
                        # Update progress
                        pct = int((idx / total) * 100)
                        self.progress.config(value=pct)
                        self.progress_label.config(text=f"{pct}%")
                        continue
                    
                    # Use function from module
                    slice_count = process_subject_to_2d(
                        brain_path, 
                        self.dataset_2d_dir.get(), 
                        OUT_SIZE, 
                        NUM_SLICES,
                        self.log  # Pass log callback
                    )
                    
                    processed += 1
                    
                    # Update progress bar and percentage label
                    pct = int((idx / total) * 100)
                    self.progress.config(value=pct)
                    self.progress_label.config(text=f"{pct}%")
                
                self.log(f"\n✓ Completed 2D dataset creation!")
                self.log(f"   - Processed: {processed} images")
                self.log(f"   - Skipped: {skipped} images (already exist)")
                if standalone:
                    messagebox.showinfo("Success", f"2D dataset creation completed!\nProcessed: {processed} images\nSkipped: {skipped} images")
                
            except Exception as e:
                self.log(f"\n✗ ERROR: {str(e)}")
                if standalone:
                    messagebox.showerror("Error", str(e))
            finally:
                if standalone:
                    self.progress.config(value=0)
                    self.progress_label.config(text="")
                    self.status_label.config(text="Ready")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_assign_labels(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Warning", "A process is already running!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(4):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.config(mode="determinate", value=0)
            self.status_label.config(text="Assigning labels...")
        
        def task():
            self.log("=" * 60)
            self.log("[STEP 4] STARTING LABEL ASSIGNMENT")
            self.log("=" * 60)
            
            try:
                # Import processing functions from assign_labels module
                from assign_labels import load_label_map, assign_labels_for_subject
                
                os.makedirs(self.labeled_dir.get(), exist_ok=True)
                
                # Get selected labels
                selected_labels = []
                if self.label_cn.get():
                    selected_labels.append("CN")
                if self.label_emci.get():
                    selected_labels.append("EMCI")
                if self.label_lmci.get():
                    selected_labels.append("LMCI")
                if self.label_smc.get():
                    selected_labels.append("SMC")
                if self.label_ad.get():
                    selected_labels.append("AD")
                
                self.log(f"Selected labels: {', '.join(selected_labels)}")
                self.log("")
                
                # Use function load_label_map from module
                label_map = load_label_map(self.csv_path.get())
                
                # Đếm tổng số subject cần xử lý
                all_subjects = [subj for subj in os.listdir(self.dataset_2d_dir.get()) 
                               if os.path.isdir(os.path.join(self.dataset_2d_dir.get(), subj))]
                total = len(all_subjects)
                self.log(f"Total subjects: {total}")
                
                processed = 0
                skipped = 0
                filtered = 0
                
                for idx, subj in enumerate(all_subjects, 1):
                    subj_dir = os.path.join(self.dataset_2d_dir.get(), subj)
                    
                    if subj not in label_map:
                        self.log(f"[SKIP] No label: {subj}")
                        skipped += 1
                        # Update progress
                        pct = int((idx / total) * 100)
                        self.progress.config(value=pct)
                        self.progress_label.config(text=f"{pct}%")
                        continue
                    
                    label = label_map[subj]
                    
                    # Check if this label is selected
                    if label not in selected_labels:
                        self.log(f"[FILTER] {subj} → {label} (not selected)")
                        filtered += 1
                        # Update progress
                        pct = int((idx / total) * 100)
                        self.progress.config(value=pct)
                        self.progress_label.config(text=f"{pct}%")
                        continue
                    
                    # Check if subject has already been processed (check the first file)
                    out_label_dir = os.path.join(self.labeled_dir.get(), label)
                    first_file = os.path.join(out_label_dir, f"{subj}_000.png")
                    if os.path.exists(first_file):
                        self.log(f"[SKIP] Already exists: {subj} → {label}")
                        skipped += 1
                        # Update progress
                        pct = int((idx / total) * 100)
                        self.progress.config(value=pct)
                        self.progress_label.config(text=f"{pct}%")
                        continue
                    
                    # Use function from module
                    slice_count = assign_labels_for_subject(
                        subj_dir, 
                        subj, 
                        label, 
                        self.labeled_dir.get(), 
                        self.log
                    )
                    
                    if slice_count > 0:
                        processed += 1
                    
                    # Update progress bar and percentage label
                    pct = int((idx / total) * 100)
                    self.progress.config(value=pct)
                    self.progress_label.config(text=f"{pct}%")
                
                self.log(f"\n✓ Label assignment completed!")
                self.log(f"   - Processed: {processed} subjects")
                self.log(f"   - Filtered (label not selected): {filtered} subjects")
                self.log(f"   - Skipped (no label/already exist): {skipped} subjects")
                if standalone:
                    messagebox.showinfo("Success", f"Label assignment completed!\nProcessed: {processed} subjects\nFiltered: {filtered} subjects\nSkipped: {skipped} subjects")
                
            except Exception as e:
                self.log(f"\n✗ ERROR: {str(e)}")
                if standalone:
                    messagebox.showerror("Error", str(e))
            finally:
                if standalone:
                    self.progress.config(value=0)
                    self.progress_label.config(text="")
                    self.status_label.config(text="Ready")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_split_dataset(self, standalone=True):
        if standalone and self.is_running:
            messagebox.showwarning("Warning", "A process is already running!")
            return
        
        if standalone:
            # Validate inputs
            if not self.validate_inputs(5):
                return
        
        if standalone:
            self.is_running = True
            self.set_buttons_state(tk.DISABLED)
            self.progress.start()
            self.status_label.config(text="Splitting dataset...")
        
        def task():
            self.log("=" * 60)
            self.log("[STEP 5] STARTING DATA SPLIT")
            self.log("=" * 60)
            
            try:
                # Import function from split_dataset module
                from split_dataset import split_dataset_by_subject
                
                # Get parameters
                train_r = float(self.train_ratio.get())
                val_r = float(self.val_ratio.get())
                test_r = float(self.test_ratio.get())
                seed = int(self.random_seed.get())
                
                # Get selected labels
                selected_labels = []
                if self.label_cn.get():
                    selected_labels.append("CN")
                if self.label_emci.get():
                    selected_labels.append("EMCI")
                if self.label_lmci.get():
                    selected_labels.append("LMCI")
                if self.label_smc.get():
                    selected_labels.append("SMC")
                if self.label_ad.get():
                    selected_labels.append("AD")
                
                self.log(f"Configuration:")
                self.log(f"  - Train: {train_r*100:.1f}%")
                self.log(f"  - Validation: {val_r*100:.1f}%")
                self.log(f"  - Test: {test_r*100:.1f}%")
                self.log(f"  - Random Seed: {seed}")
                self.log(f"  - Selected Labels: {', '.join(selected_labels) if selected_labels else 'All'}")
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
                        random_seed=seed,
                        selected_labels=selected_labels if selected_labels else None
                    )
                finally:
                    __builtins__.print = original_print
                
                self.log("\n✓ Data split completed!")
                if standalone:
                    messagebox.showinfo("Success", "Data split completed!")
                
            except Exception as e:
                self.log(f"\n✗ ERROR: {str(e)}")
                if standalone:
                    messagebox.showerror("Error", str(e))
            finally:
                if standalone:
                    self.progress.stop()
                    self.status_label.config(text="Ready")
                    self.is_running = False
                    self.set_buttons_state(tk.NORMAL)
        
        if standalone:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()
    
    def run_all(self):
        if self.is_running:
            messagebox.showwarning("Warning", "A process is already running!")
            return
        
        # Validate inputs
        if not self.validate_inputs("all"):
            return
        
        response = messagebox.askyesno("Confirmation", 
                                       "Run the entire process?\n\n" +
                                       "1. Skull Stripping\n" +
                                       "2. MNI Registration\n" +
                                       "3. Create 2D Data\n" +
                                       "4. Assign Labels\n" +
                                       "5. Data Split")
        if not response:
            return
        
        self.is_running = True
        self.set_buttons_state(tk.DISABLED)
        self.progress.config(mode="indeterminate")
        self.progress.start()
        
        def task():
            self.log("\n" + "=" * 60)
            self.log("STARTING FULL PROCESS")
            self.log("=" * 60 + "\n")
            
            try:
                # Step 1
                self.status_label.config(text="Step 1/5: Skull Stripping...")
                self.run_skull_stripping(standalone=False)
                
                # Step 2
                self.status_label.config(text="Step 2/5: MNI Registration...")
                self.run_mni_registration(standalone=False)
                
                # Step 3
                self.status_label.config(text="Step 3/5: Create 2D Data...")
                self.run_make_2d(standalone=False)
                
                # Step 4
                self.status_label.config(text="Step 4/5: Assign Labels...")
                self.run_assign_labels(standalone=False)
                
                # Step 5
                self.status_label.config(text="Step 5/5: Data Split...")
                self.run_split_dataset(standalone=False)
                
                self.log("\n" + "=" * 60)
                self.log("✓ FULL PROCESS COMPLETED!")
                self.log("=" * 60)
                
                messagebox.showinfo("Success", "The entire process has completed!")
                
            finally:
                self.progress.stop()
                self.status_label.config(text="Ready")
                self.is_running = False
                self.set_buttons_state(tk.NORMAL)
        
        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ADNIProcessorGUI(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\n[STOPPED] Program interrupted.")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
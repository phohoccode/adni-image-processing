import torch
import torch.nn as nn
import torchvision.models as models

# ==========================================
# 1. Nhánh Hình ảnh (CNN Branch)
# ==========================================
class CNNBranch(nn.Module):
    def __init__(self, embedding_dim=128):
        super(CNNBranch, self).__init__()
        # Sử dụng ResNet18 làm backbone (nhẹ và hiệu quả cho ảnh y tế)
        # pretrained=True giúp hội tụ nhanh hơn
        resnet = models.resnet18(pretrained=True)
        
        # Loại bỏ lớp phân loại cuối cùng (fc) của ResNet gốc
        self.features = nn.Sequential(*list(resnet.children())[:-1])
        
        # Thêm một lớp Linear để nén đặc trưng về kích thước mong muốn (ví dụ: 128)
        self.fc = nn.Linear(512, embedding_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        # x shape: [Batch_Size, 3, 224, 224] (Hoặc 1 kênh nếu bạn sửa input layer)
        x = self.features(x)         # Output: [Batch, 512, 1, 1]
        x = x.view(x.size(0), -1)    # Flatten: [Batch, 512]
        x = self.dropout(x)
        x = self.fc(x)               # Output: [Batch, embedding_dim]
        return self.relu(x)

# ==========================================
# 2. Nhánh Lâm sàng (MLP Branch)
# ==========================================
class MLPBranch(nn.Module):
    def __init__(self, input_dim, embedding_dim=32):
        super(MLPBranch, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(64, embedding_dim),
            nn.ReLU()
        )

    def forward(self, x):
        # x shape: [Batch_Size, số_lượng_chỉ_số_lâm_sàng]
        return self.net(x) # Output: [Batch, embedding_dim]

# ==========================================
# 3. Lớp Attention Fusion (Trái tim của mô hình)
# ==========================================
class AttentionFusion(nn.Module):
    def __init__(self, cnn_dim, mlp_dim, hidden_dim=64):
        super(AttentionFusion, self).__init__()
        # Mạng học trọng số Attention
        self.attention_net = nn.Sequential(
            nn.Linear(cnn_dim + mlp_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1), # Output ra 1 điểm số (score)
            nn.Sigmoid()              # Đưa về khoảng [0, 1] để làm gate
        )
        
    def forward(self, cnn_feat, mlp_feat):
        # Nối 2 vector đặc trưng lại
        combined = torch.cat((cnn_feat, mlp_feat), dim=1)
        
        # Tính toán trọng số Attention (alpha)
        # Alpha cho biết mức độ quan trọng của sự kết hợp này
        alpha = self.attention_net(combined)
        
        # Áp dụng Attention lên đặc trưng CNN (Gated Mechanism)
        # Ý nghĩa: Dùng thông tin lâm sàng để "lọc" thông tin hình ảnh
        # Nếu MLP bảo "ca này không giống AD", alpha sẽ giảm nhiễu từ CNN
        weighted_cnn = cnn_feat * alpha
        
        # Trả về vector đã được tổng hợp
        return torch.cat((weighted_cnn, mlp_feat), dim=1)

# ==========================================
# 4. Mô hình Tổng hợp (Full Multimodal Model)
# ==========================================
class ADNI_Multimodal_Model(nn.Module):
    def __init__(self, num_clinical_features, num_classes=3):
        super(ADNI_Multimodal_Model, self).__init__()
        
        # Khai báo các nhánh con
        self.cnn = CNNBranch(embedding_dim=128)
        self.mlp = MLPBranch(input_dim=num_clinical_features, embedding_dim=32)
        
        # Khai báo lớp Fusion
        self.fusion = AttentionFusion(cnn_dim=128, mlp_dim=32)
        
        # Lớp phân loại cuối cùng (Classification Head)
        # Input là tổng kích thước của CNN (đã qua attention) và MLP
        self.classifier = nn.Sequential(
            nn.Linear(128 + 32, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes) # Output: [CN, MCI, AD]
        )

    def forward(self, image, clinical_data):
        # 1. Trích xuất đặc trưng từ từng nhánh
        img_feat = self.cnn(image)        # [Batch, 128]
        clin_feat = self.mlp(clinical_data) # [Batch, 32]
        
        # 2. Hợp nhất bằng Attention
        fused_feat = self.fusion(img_feat, clin_feat) # [Batch, 160]
        
        # 3. Phân loại
        output = self.classifier(fused_feat)
        return output

# ==========================================
# 5. Kiểm tra thử (Dummy Run)
# ==========================================
if __name__ == "__main__":
    # Giả lập dữ liệu đầu vào
    batch_size = 4
    
    # Giả sử ảnh đầu vào kích thước 224x224, 3 kênh màu (RGB)
    # Lưu ý: Nếu ảnh grayscale (1 kênh), cần sửa input layer của ResNet hoặc lặp lại kênh 3 lần
    dummy_img = torch.randn(batch_size, 3, 224, 224)
    
    # Giả sử có 7 chỉ số lâm sàng (Age, Gender, Edu, APOE4, MMSE, CDR, FAQ)
    dummy_clinical = torch.randn(batch_size, 7)
    
    # Khởi tạo mô hình
    model = ADNI_Multimodal_Model(num_clinical_features=7, num_classes=3)
    
    # Chạy thử
    output = model(dummy_img, dummy_clinical)
    
    print("Kích thước đầu ra:", output.shape) # Mong đợi: [4, 3]
    print("Giá trị dự đoán (Logits):", output)
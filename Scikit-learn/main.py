# ============================
# PHÂN LOẠI 4 LOÀI HOA IRIS BẰNG KNN
# ============================

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1️⃣ Tải dữ liệu Iris
iris = load_iris()
X = iris.data
y = iris.target

# (Tuỳ chọn) Thêm loài thứ 4 Iris siberica (dữ liệu giả lập)
new_flowers = np.random.rand(30, 4) * [7.5, 4.0, 6.5, 2.5]
new_labels = np.array([3]*30)
X = np.vstack([X, new_flowers])
y = np.hstack([y, new_labels])
target_names = list(iris.target_names) + ["iris-siberica"]

# 2️⃣ Chia dữ liệu Train/Test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3️⃣ Chuẩn hóa dữ liệu
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# 4️⃣ Huấn luyện mô hình KNN
model = KNeighborsClassifier(n_neighbors=5)
model.fit(X_train, y_train)

# 5️⃣ Dự đoán
y_pred = model.predict(X_test)

# 6️⃣ Đánh giá mô hình
print("🎯 Báo cáo phân loại:\n")
print(classification_report(y_test, y_pred, target_names=target_names))

# 7️⃣ Ma trận nhầm lẫn (Confusion Matrix)
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, cmap="Greens", fmt="d",
            xticklabels=target_names, yticklabels=target_names)
plt.title("Confusion Matrix - Iris Classification (KNN)")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# 8️⃣ Trực quan hóa (2D PCA)
from sklearn.decomposition import PCA
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X)

plt.figure(figsize=(8,6))
for i, label in enumerate(np.unique(y)):
    plt.scatter(X_pca[y == label, 0], X_pca[y == label, 1], label=target_names[i])
plt.title("Phân bố 4 loài hoa Iris sau khi giảm chiều PCA (2D)")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.legend()
plt.show()

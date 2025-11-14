import sqlite3
import pandas as pd
import numpy as np
import re
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

db_path = "/Users/trithuan/Desktop/Python/BaiTapLon2/data_premierleague_2024_25/premierleague_2024_25.db"
conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT * FROM player_stats", conn)
conn.close()

numeric_cols = []
for col in df.columns:
    is_num = True
    for v in df[col].dropna().head(10):
        v_str = str(v).strip()
        if not re.match(r"^[0-9\.,%-]+$", v_str):
            is_num = False
            break
    if is_num:
        numeric_cols.append(col)

df_numeric = df[numeric_cols].copy()

df_numeric = df_numeric.replace({
    r'(?i)^n/?a$': np.nan,
    r',': '.',  
    r'%': ''
}, regex=True)

df_numeric = df_numeric.astype(float)
df_numeric = df_numeric.fillna(df_numeric.mean())

kmeans = KMeans(n_clusters=3, random_state=42)
df["Cluster"] = kmeans.fit_predict(df_numeric)

pca_2d = PCA(n_components=2)
X_pca_2d = pca_2d.fit_transform(df_numeric)

plt.figure(figsize=(8, 6))
plt.scatter(
    X_pca_2d[:, 0],   # tọa độ trục X = PCA thành phần 1
    X_pca_2d[:, 1],   # tọa độ trục Y = PCA thành phần 2
    c=df["Cluster"],  # màu theo nhãn cụm đã phân loại
    cmap="viridis",   # bảng màu viridis
    s=40              # kích thước mỗi điểm
)
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.title("PCA 2D - Visualization of Clusters (K = 3)")
plt.colorbar(label="Cluster")
plt.grid(True)
plt.show()

pca_3d = PCA(n_components=3)
X_pca_3d = pca_3d.fit_transform(df_numeric)

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

sc = ax.scatter(
    X_pca_3d[:, 0],   # tọa độ trục X = PCA 1
    X_pca_3d[:, 1],   # tọa độ trục Y = PCA 2
    X_pca_3d[:, 2],   # tọa độ trục Z = PCA 3
    c=df["Cluster"],  # màu theo cụm K-means
    cmap="viridis",   # bảng màu viridis
    s=40              # kích thước mỗi điểm
)

ax.set_xlabel("PC1")
ax.set_ylabel("PC2")
ax.set_zlabel("PC3")
ax.set_title("PCA 3D - Visualization of Clusters (K = 3)")
fig.colorbar(sc, label="Cluster")

plt.show()

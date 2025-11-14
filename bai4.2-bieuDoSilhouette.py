from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
import numpy as np
import re

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

k = 3
kmeans = KMeans(n_clusters=k, random_state=42)
cluster_labels = kmeans.fit_predict(df_numeric)

sil_vals = silhouette_samples(df_numeric, cluster_labels)
avg_sil = silhouette_score(df_numeric, cluster_labels)

fig, ax1 = plt.subplots(figsize=(8, 5))
y_lower = 10

for i in range(k):
    ith_vals = sil_vals[cluster_labels == i]
    ith_vals.sort()
    size_i = ith_vals.shape[0]

    ax1.fill_betweenx(np.arange(y_lower, y_lower + size_i),
                      0, ith_vals, alpha=0.7)
    y_lower += size_i + 10

ax1.axvline(x=avg_sil, color="red", linestyle="--", linewidth=2)
ax1.set_title("Silhouette Plot for K = 3")
ax1.set_xlabel("Silhouette Value")
ax1.set_ylabel("Cluster")

plt.tight_layout()
plt.show()

print("Giá trị Silhouette trung bình (K=3):", avg_sil)

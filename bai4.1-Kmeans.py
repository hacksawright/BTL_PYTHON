from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
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
        if not re.match(r"^[0-9\.,%-]+$", str(v).strip()):
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

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_numeric)

kmeans = KMeans(n_clusters=3, random_state=42)
df["Cluster"] = kmeans.fit_predict(X_scaled)

print("Đã phân cụm cầu thủ thành 3 nhóm!")
print(df["Cluster"].value_counts())

print(df.head())

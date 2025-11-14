from sklearn.cluster import KMeans
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

sse = []
K_range = range(1, 11)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(df_numeric)
    sse.append(kmeans.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(K_range, sse, 'o-', linewidth=2)
plt.title("Elbow Method to Determine Optimal K")
plt.xlabel("K")
plt.ylabel("SSE (Inertia)")
plt.grid(True)
plt.show()
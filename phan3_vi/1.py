import sqlite3
import pandas as pd
import numpy as np

# --- Đường dẫn database và file CSV đầu ra ---
DB_PATH = "data_premierleague_2024_25/premierleague_2024_25.db"
OUT_CSV = "team_stats_summary.csv"

# --- Kết nối database ---
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM player_stats", conn)


# --- Xác định cột chứa tên đội bóng ---
team_col = None
for c in df.columns:
    if 'team' in c.lower():
        team_col = c
        break

# --- Tự động ép kiểu các cột có vẻ là số ---
exclude_keywords = ['player', 'team', 'unnamed: 1_level_0_nation']
for c in df.columns:
    if c not in [team_col] and all(k not in c.lower() for k in exclude_keywords):
        try:
            numeric_test = pd.to_numeric(df[c], errors='coerce')
            ratio_numeric = numeric_test.notna().mean()
            if ratio_numeric > 0.8:
                df[c] = numeric_test
        except Exception:
            pass

# --- Lấy danh sách cột số sau khi ép ---
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
numeric_cols = [c for c in numeric_cols if not any(x in c.lower() for x in ['id', '_id', 'index'])]


# --- Tính trung vị, trung bình, độ lệch chuẩn cho từng đội ---
agg_funcs = {col: ['median', 'mean', 'std'] for col in numeric_cols}
grouped = df.groupby(team_col)[numeric_cols].agg(agg_funcs)
grouped.columns = [f"{col}_{stat}" for col, stat in grouped.columns]
grouped = grouped.reset_index()

# --- Xuất ra file CSV ---
grouped.to_csv(OUT_CSV, index=False)
print(f"\n✅ Đã lưu kết quả vào file: {OUT_CSV}")

# --- Tìm đội bóng có chỉ số cao nhất ở mỗi chỉ số ---
# Sử dụng tổng điểm của từng đội
team_stats_sum = df.groupby(team_col)[numeric_cols].sum()
best_teams = {col: (team_stats_sum[col].idxmax(), team_stats_sum[col].max()) for col in numeric_cols}

print("\n✅ Đội bóng có chỉ số cao nhất ở mỗi chỉ số:")
for stat, (team, value) in best_teams.items():
    print(f"{stat}: {team} ({value})")
# --- Tính phong độ tổng thể và chọn đội tốt nhất ---
team_stats_sum = team_stats_sum.copy()  # tránh PerformanceWarning
team_stats_sum['total_points'] = team_stats_sum.sum(axis=1)
team_stats_sum = team_stats_sum.sort_values(by='total_points', ascending=False)

best_overall_team = team_stats_sum.index[0]
best_total_points = team_stats_sum['total_points'].iloc[0]
print(f"\n🏆 Đội có phong độ tổng thể tốt nhất: {best_overall_team} ({best_total_points} điểm)")

# --- Đóng kết nối ---
conn.close()

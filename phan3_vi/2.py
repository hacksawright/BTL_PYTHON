
import re
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
import joblib
import warnings
warnings.filterwarnings("ignore")

DB_PATH = "trung.db"

def norm_name(s):
    if pd.isna(s): return s
    s = str(s).lower().strip()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[^a-z0-9\s]', '', s)
    return s.strip()

def parse_market_value(v):
    if pd.isna(v): return np.nan
    s = str(v).lower().replace('€','').replace('eur','').replace(',','').strip()
    m = re.match(r'([0-9]*\.?[0-9]+)\s*([mk]?)', s)
    if m:
        num = float(m.group(1))
        unit = m.group(2)
        if unit == 'm': return num * 1e6
        if unit == 'k': return num * 1e3
        return num
    s2 = re.sub(r'[^\d\.]', '', s)
    try:
        return float(s2)
    except:
        return np.nan

# -------------------------
# 1. Đọc dữ liệu từ DB
# -------------------------
conn = sqlite3.connect(DB_PATH)
player_stats = pd.read_sql("SELECT * FROM player_stats;", conn)
value_tbl = pd.read_sql("SELECT * FROM value_premier_league_90;", conn)
conn.close()
# 🧹 Loại bỏ các dòng tổng hợp đội bóng (ví dụ "Squad Total", "Team Total", ...)
player_stats = player_stats[~player_stats['Player'].str.contains('total|overall|average', case=False, na=False)]

# -------------------------
# 2. Chuẩn hoá tên cầu thủ và gộp dữ liệu
# -------------------------
player_stats['_player_norm'] = player_stats['Player'].apply(norm_name)
value_tbl['_player_norm'] = value_tbl['player'].apply(norm_name)

value_tbl['market_value_num'] = value_tbl['market_value'].apply(parse_market_value)
value_tbl['market_value_million'] = value_tbl['market_value_num'] / 1e6

df = player_stats.merge(value_tbl[['_player_norm','market_value_million']], on='_player_norm', how='left')

print("Tổng số cầu thủ:", len(df))
print("Có dữ liệu định giá:", df['market_value_million'].notna().sum())

# -------------------------
# 3. Chuẩn hoá vị trí cầu thủ
# -------------------------
def normalize_position(v):
    if pd.isna(v): return np.nan
    s = str(v).lower()
    if 'gk' in s or 'goal' in s: return 'GK'
    if any(x in s for x in ['def','cb','lb','rb']): return 'DEF'
    if any(x in s for x in ['mid','cm','cam','mf']): return 'MID'
    if any(x in s for x in ['fw','st','striker','forward','cf']): return 'FWD'
    return np.nan

df['Position_group'] = df['Unnamed: 2_level_0_Pos'].apply(normalize_position)
print("Số lượng theo vị trí:\n", df['Position_group'].value_counts(dropna=False))

# -------------------------
# 4. Chuyển các cột chuỗi có toàn số sang dạng float
# -------------------------
for c in df.columns:
    if df[c].dtype == 'object':
        # nếu >90% giá trị trong cột là số (hoặc NaN) thì ép kiểu
        try:
            numeric_part = pd.to_numeric(df[c], errors='coerce')
            ratio_numeric = numeric_part.notna().mean()
            if ratio_numeric > 0.9:  # ngưỡng tin cậy
                df[c] = numeric_part.fillna(0)
        except:
            pass

# -------------------------
# 5. Chọn các cột số để train
# -------------------------
num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['market_value_million']]
train_df = df[df['market_value_million'].notna()].copy()

X_train = train_df[num_cols]
y_train = train_df['market_value_million']

imp = SimpleImputer(strategy='median')
X_imp = imp.fit_transform(X_train)

# -------------------------
# 6. Huấn luyện mô hình
# -------------------------
model = RandomForestRegressor(n_estimators=300, random_state=42)
X_tr, X_te, y_tr, y_te = train_test_split(X_imp, y_train, test_size=0.2, random_state=42)
model.fit(X_tr, y_tr)

y_pred = model.predict(X_te)
print("\nHiệu quả mô hình:")
print("MAE:", mean_absolute_error(y_te, y_pred))
print("RMSE:", np.sqrt(mean_squared_error(y_te, y_pred)))
print("R2:", r2_score(y_te, y_pred))

# -------------------------
# 7. Dự đoán và lưu kết quả
# -------------------------
df['predicted_value_million'] = model.predict(imp.transform(df[num_cols]))

output_df = df[['Player', 'Team', 'Position_group', 'market_value_million', 'predicted_value_million']]
output_df.to_csv("player_valuation_results.csv", index=False)


print("\n✅ Đã lưu kết quả ra file player_valuation_results.csv ")

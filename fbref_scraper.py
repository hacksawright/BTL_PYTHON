import pandas as pd
import sqlite3
from bs4 import BeautifulSoup, Comment
from io import StringIO

HTML_FILE = "premier_league_2024_2025_stats.html"

print("📂 Đang đọc dữ liệu từ file HTML đã lưu...")

# Đọc file HTML
with open(HTML_FILE, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

# Tìm bảng bị ẩn trong comment
comments = soup.find_all(string=lambda text: isinstance(text, Comment))
table_html = None
for c in comments:
    if "table" in c and "stats_standard" in c:
        table_html = c
        break

if table_html is None:
    raise Exception("❌ Không tìm thấy bảng cầu thủ (stats_standard). Hãy kiểm tra lại file HTML!")

# Đọc bảng
df = pd.read_html(StringIO(str(table_html)))[0]

# Chuẩn hoá tên cột (xoá khoảng trắng, xử lý multiindex)
df.columns = [col[1] if isinstance(col, tuple) else col for col in df.columns]
df.columns = [str(c).strip() for c in df.columns]

# Xử lý trùng tên cột (ví dụ: Gls, Ast lặp lại)
cols = []
for c in df.columns:
    if c in cols:
        i = 2
        new_c = f"{c}_{i}"
        while new_c in cols:
            i += 1
            new_c = f"{c}_{i}"
        cols.append(new_c)
    else:
        cols.append(c)
df.columns = cols

# Kiểm tra cột Player có tồn tại
if "Player" not in df.columns:
    print("⚠️ Các cột hiện có:", df.columns.tolist())
    raise Exception("Không thể xác định cột 'Player'!")

# Làm sạch dữ liệu
df = df[df["Player"] != "Player"]
df = df.dropna(subset=["Player"])
df["Min"] = df["Min"].astype(str).str.replace(",", "").astype(float)
df = df[df["Min"] > 90]
df = df.fillna("N/a")

# Lưu vào SQLite
conn = sqlite3.connect("players.db")
df.to_sql("premier_league_2024_2025", conn, if_exists="replace", index=False)
conn.close()

print(f"✅ Đã lưu {len(df)} cầu thủ vào cơ sở dữ liệu SQLite (players.db)!")
print(f"📊 Các cột gồm: {', '.join(df.columns)}")

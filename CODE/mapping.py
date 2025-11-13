import sqlite3
from fuzzywuzzy import fuzz
import re

# ------------------- 1. Tiền xử lý tên cầu thủ -------------------
def normalize_name(name):
    if not name:
        return ""
    # Chuyển về lowercase
    name = name.strip().lower()
    # Xóa dấu . và khoảng trắng thừa
    name = re.sub(r'\.', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    # Xóa các từ không quan trọng (nếu muốn)
    # name = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', name)
    return name.strip()

# ------------------- 2. Tạo dict value theo tên đã normalize -------------------
conn = sqlite3.connect("premierleague_2024_25.db")
cursor = conn.cursor()

# Lấy hết value_transfer → dict {normalized_name: (original_name, market_value)}
value_dict = {}
cursor.execute("SELECT team, player, market_value FROM value_transfer_2024_2025")
for team, player, mv in cursor.fetchall():
    if mv == 'N/A' or not mv:
        continue
    norm = normalize_name(player)
    # Nếu đã có tên tương tự → giữ thằng value cao hơn (thường là tên đầy đủ)
    if norm not in value_dict or len(player) > len(value_dict[norm][0]):
        value_dict[norm] = (player, mv, team)

print(f"Đã load {len(value_dict)} cầu thủ từ value_transfer")

# ------------------- 3. So sánh fuzzy & gán value -------------------
cursor.execute("""
SELECT rowid, team, player 
FROM player_stats 
WHERE player IS NOT NULL 
  AND TRIM(player) != ''
  AND LOWER(player) NOT LIKE '%total%'
  AND LOWER(player) NOT LIKE '%opponent%'
  AND LOWER(player) NOT LIKE '%squad%'
ORDER BY rowid
""")
rows = cursor.fetchall()

updates = []
matched = 0
total = len(rows)

for rowid, team_ps, player_ps in rows:
    norm_ps = normalize_name(player_ps)
    best_score = 0
    best_value = 'N/A'
    best_orig_name = ''

    # Duyệt tất cả value (chỉ ~500-600 cầu thủ PL → nhanh lắm)
    for norm_v, (orig_name, mv, team_v) in value_dict.items():
        # Ưu tiên cùng đội trước
        score = fuzz.ratio(norm_ps, norm_v)
        if team_ps.lower() == team_v.lower():
            score += 15  # bonus 15 điểm nếu cùng đội

        if score > best_score:
            best_score = score
            best_value = mv
            best_orig_name = orig_name

    # Ngưỡng 85 là cực chuẩn (có thể hạ xuống 80 nếu muốn bắt thêm)
    if best_score >= 85:
        matched += 1
        updates.append((best_value, best_orig_name, best_score, rowid))
    else:
        updates.append(('N/A', '', 0, rowid))

print(f"Đang ghi {matched}/{total} cầu thủ đã khớp...")

# ------------------- 4. Tạo bảng mới chỉ 3 cột -------------------
cursor.execute("DROP TABLE IF EXISTS value_premier_league_90")
cursor.execute("""
CREATE TABLE value_premier_league_90 (
    team TEXT,
    player TEXT,
    market_value TEXT
)
""")

insert_sql = "INSERT INTO value_premier_league_90 (team, player, market_value) VALUES (?, ?, ?)"
for i, (rowid, team_ps, player_ps) in enumerate(rows):
    mv = updates[i][0]
    cursor.execute(insert_sql, (team_ps, player_ps, mv))

conn.commit()

# ------------------- 5. In báo cáo chi tiết -------------------
print("\n=== KẾT QUẢ KHỚP ===")
print(f"Khớp thành công: {matched}/{total} ({matched/total*100:.1f}%)")

# In 20 thằng score thấp nhất để sửa tay (nếu cần)
print("\n--- 20 cầu thủ KHÓ KHỚP NHẤT (score < 90) ---")
cursor.execute("""
SELECT team, player, market_value 
FROM value_premier_league_90 
WHERE market_value = 'N/A'
LIMIT 20
""")
for row in cursor.fetchall():
    print(row)

conn.close()
print("\nHOÀN TẤT! Bảng value_premier_league_90 đã sẵn sàng, chỉ 3 cột, thứ tự y hệt player_stats.")
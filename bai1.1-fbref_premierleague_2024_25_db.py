from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time, re, sqlite3, os
from io import StringIO

# ============================
# ⚽ Danh sách đội Premier League 2024-25
# ============================
teams = {
    "Arsenal": "18bb7c10",
    "Aston Villa": "8602292d",
    "Bournemouth": "4ba7cbea",
    "Brentford": "cd051869",
    "Brighton": "d07537b9",
    "Chelsea": "cff3d9bb",
    "Crystal Palace": "47c64c55",
    "Everton": "d3fd31cc",
    "Fulham": "fd962109",
    "Ipswich Town": "facb2d1d",
    "Leicester City": "a2d435b3",
    "Liverpool": "822bd0ba",
    "Manchester City": "b8fd03ef",
    "Manchester Utd": "19538871",
    "Newcastle Utd": "b2b47a98",
    "Nottingham Forest": "e4a775cb",
    "Southampton": "33c895d4",
    "Tottenham": "361ca564",
    "West Ham": "7c21e445",
    "Wolves": "8cec06e1"
}

SEASON = "2024-2025"
BASE_URL = "https://fbref.com/en/squads/"
DATA_DIR = "data_premierleague_2024_25"
os.makedirs(DATA_DIR, exist_ok=True)

# Selenium setup
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-infobars")
options.add_argument("--start-maximized")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="MacIntel",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)

all_teams_data = []

def scrape_team(team_name, team_id):
    url = f"{BASE_URL}{team_id}/{SEASON}/{team_name.replace(' ', '-')}-Stats"
    print(f"\n⚽ Đang cào dữ liệu {team_name} ({url})")
    driver.get(url)
    time.sleep(7)

    # Cuộn để load hết dữ liệu
    for _ in range(4):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # Mở các bảng bị ẩn trong comment HTML
    js_uncomment = """
    let walker = document.createTreeWalker(document.body, NodeFilter.SHOW_COMMENT, null, false);
    let comments = [];
    while(walker.nextNode()) comments.push(walker.currentNode);
    for (let c of comments) {
        let span = document.createElement('span');
        span.innerHTML = c.textContent;
        c.parentNode.insertBefore(span, c);
    }
    """
    driver.execute_script(js_uncomment)
    time.sleep(2)

    html_source = driver.execute_script("return document.body.innerHTML")
    soup = BeautifulSoup(html_source, "html.parser")
    tables = soup.find_all("table", id=re.compile("stats_"))

    print(f"{team_name}: phát hiện {len(tables)} bảng sau render")

    merged_team = None
    for i, table in enumerate(tables, start=1):
        table_id = table.get("id", f"table_{i}")
        try:
            df = pd.read_html(StringIO(str(table)))[0]

            # Gộp multi-index header thành 1 cấp
            df.columns = ["_".join(col).strip() if isinstance(col, tuple) else col for col in df.columns]

            player_cols = [c for c in df.columns if "Player" in c]
            if not player_cols:
                continue

            df.rename(columns={player_cols[0]: "Player"}, inplace=True)
            df["Team"] = team_name

            # Gộp dữ liệu các bảng
            if merged_team is None:
                merged_team = df
            else:
                merged_team = pd.merge(merged_team, df, on="Player", how="outer", suffixes=("", f"_{table_id}"))
        except Exception:
            continue

    if merged_team is None:
        print(f"{team_name}: Không lấy được dữ liệu")
        return None

    df = merged_team.fillna("N/a")

    seen = set()
    unique_cols = []
    for col in df.columns:
        if col not in seen:
            unique_cols.append(col)
            seen.add(col)
    df = df[unique_cols]

    to_drop = []
    cols = df.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            try:
                if df[cols[i]].equals(df[cols[j]]):
                    to_drop.append(cols[j])
            except:
                pass
    df.drop(columns=list(set(to_drop)), inplace=True, errors="ignore")

    min_cols = [c for c in df.columns if "Playing Time_Min" in c]

    if min_cols:
        col_min = min_cols[0]

        df[col_min] = (
            df[col_min]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.extract(r"(\d+)")[0]
            .astype(float)
        )

        df = df[df[col_min] > 90]
    else:
        print(f"{team_name}: Không tìm thấy cột 'Playing Time_Min' để lọc.")
       
    print(f"{team_name}: {len(df)} cầu thủ, {len(df.columns)} cột sau làm sạch")

    all_teams_data.append(df)
    return df

for team_name, team_id in teams.items():
    try:
        scrape_team(team_name, team_id)
    except Exception as e:
        print(f"Lỗi {team_name}: {e}")
        continue

if all_teams_data:
    combined = pd.concat(all_teams_data, ignore_index=True).fillna("N/a")
    db_path = os.path.join(DATA_DIR, "premierleague_2024_25.db")

    conn = sqlite3.connect(db_path)
    combined.to_sql("player_stats", conn, if_exists="replace", index=False)
    conn.close()

    print(f"\nHoàn tất! Dữ liệu lưu tại: {db_path}")
    print(f"Tổng cộng: {len(combined)} cầu thủ, {len(combined.columns)} cột")
else:
    print("Không có dữ liệu nào được lưu!")

driver.quit()

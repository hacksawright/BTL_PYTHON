import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ==========================
# ⚙️ Cấu hình Chrome driver
# ==========================
def setup_driver():
    chrome_options = Options()
    # Tạm thời tắt headless để debug, có thể bật lại sau
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Thêm user-agent để tránh bị phát hiện là bot
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Tắt hình ảnh để tăng tốc
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service()  # tự động nhận driver sẵn có (Selenium >= 4.10)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 30)  # Tăng thời gian chờ
    return driver, wait


# ==========================
# 📦 Danh sách đội Premier League 2024-2025
# ==========================
teams = {
    "Arsenal": "11",
    "Aston Villa": "405",
    "Bournemouth": "989",
    "Brentford": "1148",
    "Brighton": "1237",
    "Chelsea": "631",
    "Crystal Palace": "873",
    "Everton": "29",
    "Fulham": "931",
    "Ipswich Town": "677",
    "Leicester City": "1003",
    "Liverpool": "31",
    "Manchester City": "281",
    "Manchester United": "985",
    "Newcastle United": "762",
    "Nottingham Forest": "703",
    "Southampton": "180",
    "Tottenham Hotspur": "148",
    "West Ham United": "379",
    "Wolverhampton Wanderers": "543"
}


# ==========================
# 🧠 Hàm lấy giá trị cầu thủ từng đội
# ==========================
def scrape_team_values(team_name, team_id, driver, wait):
    url = f"https://www.transfermarkt.com/{team_name.lower().replace(' ', '-')}/kader/verein/{team_id}/saison_id/2024"
    print(f"\nĐang cào đội: {team_name} - {url}")
    driver.get(url)
    
    time.sleep(3)
    
    # Đóng cookie consent (giữ nguyên code của bạn)
    try:
        cookie_selectors = [
            "button#onetrust-accept-btn-handler",
            "#sp_message_container_474555 button[aria-label='Accept All']",
            "button.accept-all-cookies",
            ".cookie-consent button"
        ]
        for selector in cookie_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed():
                    btn.click()
                    print(f"  Đã đóng cookie popup")
                    time.sleep(1)
                    break
            except:
                continue
    except:
        pass

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.items")))
        time.sleep(3)

        # Scroll để load đầy đủ
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Lấy tất cả các hàng CHỈ CÓ CLASS "odd" hoặc "even" (dòng chính)
        players = driver.find_elements(By.CSS_SELECTOR, "table.items tbody tr.odd, table.items tbody tr.even")
        print(f"  Tìm thấy {len(players)} cầu thủ (chỉ dòng chính)")

        data = []
        seen_players = set()  # Tránh trùng tuyệt đối

        for row in players:
            try:
                # Lấy tên cầu thủ - ưu tiên thẻ <a> trong .hauptlink
                name_elem = row.find_element(By.CSS_SELECTOR, "td.hauptlink a")
                name = name_elem.text.strip()
                if not name or len(name) < 2:
                    continue

                # Bỏ qua nếu đã lấy rồi (phòng trường hợp vẫn bị trùng)
                if name in seen_players:
                    continue
                seen_players.add(name)

                # Lấy giá trị thị trường - ưu tiên span.werte (chứa giá trị thực)
                value = None
                try:
                    # Cách 1: Tìm span.werte trong td.rechts (chính xác nhất)
                    value_elem = row.find_element(By.CSS_SELECTOR, "td.rechts .werte")
                    value = value_elem.text.strip()
                except NoSuchElementException:
                    try:
                        # Cách 2: Tìm td.rechts.hauptlink nhưng phải chứa € hoặc số
                        value_elem = row.find_element(By.CSS_SELECTOR, "td.rechts.hauptlink")
                        value_text = value_elem.text.strip()
                        # Kiểm tra xem có phải giá trị không (phải chứa € hoặc số, KHÔNG được là tên)
                        if ("€" in value_text or any(c.isdigit() for c in value_text)) and value_text != name:
                            value = value_text
                        else:
                            # Nếu không phải, thử tìm link trong đó
                            try:
                                value_link = value_elem.find_element(By.TAG_NAME, "a")
                                value_text = value_link.text.strip()
                                # Kiểm tra lại để đảm bảo không phải tên
                                if ("€" in value_text or any(c.isdigit() for c in value_text)) and value_text != name:
                                    value = value_text
                            except:
                                pass
                    except NoSuchElementException:
                        try:
                            # Cách 3: Lấy từ td.rechts (cột cuối cùng bên phải)
                            value_elem = row.find_element(By.CSS_SELECTOR, "td.rechts")
                            value_text = value_elem.text.strip()
                            # Lọc để chỉ lấy phần có giá trị (chứa €) và không phải tên
                            if "€" in value_text and value_text != name:
                                value = value_text
                        except:
                            pass

                # Validation: Đảm bảo value không phải là tên cầu thủ và phải chứa € hoặc số
                if not value or value == name or ("€" not in value and not any(c.isdigit() for c in value)):
                    value = "N/A"

                data.append((team_name, name, value))
                print(f"    - {name}: {value}")

            except Exception as e:
                # Bỏ qua lỗi hàng
                continue

        print(f"{team_name}: {len(data)} cầu thủ hợp lệ")
        return data

    except TimeoutException:
        print(f"Không load được bảng cho {team_name}")
        driver.save_screenshot(f"debug_{team_name.replace(' ', '_')}.png")
        return []
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
        driver.save_screenshot(f"error_{team_name.replace(' ', '_')}.png")
        return []


# ==========================
# 💾 Lưu vào SQLite
# ==========================
def save_to_db(data):
    conn = sqlite3.connect("premierleague_2024_25.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS value_transfer_2024_2025 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT,
            player TEXT,
            market_value TEXT
        )
    """)

    cursor.executemany(
        "INSERT INTO value_transfer_2024_2025 (team, player, market_value) VALUES (?, ?, ?)",
        data
    )

    conn.commit()
    conn.close()
    print("💾 Dữ liệu đã lưu vào bảng value_transfer_2024_2025")


# ==========================
# 🚀 Main
# ==========================
if __name__ == "__main__":
    driver, wait = setup_driver()
    all_data = []

    for team, team_id in teams.items():
        team_data = scrape_team_values(team, team_id, driver, wait)
        all_data.extend(team_data)
        if all_data:
            save_to_db(all_data)
            print(f"\n🎯 Tổng cộng {len(all_data)} cầu thủ đã được lưu.")
        else:
            print("⚠️ Không có dữ liệu nào được lưu!")
        all_data = []
        time.sleep(2)  # tránh bị chặn

    print("Done")

    driver.quit()

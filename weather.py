import os
import requests
from datetime import datetime

# GitHubのSecretsから読み出し
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

LOCATIONS = {
    "杉並中央地域": {"lat": 35.6994, "lon": 139.6364},
    "杉並北西部":   {"lat": 35.7250, "lon": 139.6010},
    "杉並南部":     {"lat": 35.6800, "lon": 139.6150}
}

def create_web_page(curr_data, fore_data):
    """実況データと予報データを解析してHTMLを生成する"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # --- 独自ロジック判定 ---
    humidity = curr_data['main']['humidity']
    clouds = curr_data['clouds']['all']
    
    # 3時間後の雨判定（リストの最初を確認）
    next_rain = 0
    if 'rain' in fore_data['list'][0]:
        next_rain = fore_data['list'][0]['rain'].get('3h', 0)

    # 安全スコア計算 (100点満点)
    score = 100
    score -= (humidity - 50) * 1.5 if humidity > 50 else 0
    score -= clouds * 0.3
    if next_rain > 0: score = 0 

    # 判定メッセージと色の決定
    if score > 80:
        status_msg, advice, color = "最高の洗濯日和！", "今すぐ干しましょう。夕方までには乾きます。", "#2ecc71"
    elif score > 50:
        status_msg, advice, color = "干せなくはないですが…", "雲が多いか、湿度がやや高めです。", "#f1c40f"
    elif score > 0:
        status_msg, advice, color = "部屋干し推奨", "乾きが遅く、生乾き臭のリスクがあります。", "#e67e22"
    else:
        status_msg, advice, color = "【警告】今すぐ取り込んで！", "雨が近いか、既に降っています。", "#e74c3c"

    # 表形式（時系列予報）の作成
    table_rows = ""
    for item in fore_data['list'][:6]: 
        dt = datetime.fromtimestamp(item['dt']).strftime('%H:%M')
        f_temp = round(item['main']['temp'], 1)
        f_desc = item['weather'][0]['description']
        f_icon = item['weather'][0]['icon']
        icon_url = f"https://openweathermap.org/img/wn/{f_icon}.png"
        table_rows += f"<tr><td>{dt}</td><td><img src='{icon_url}' width='30'></td><td>{f_desc}</td><td>{f_temp}℃</td></tr>"

    # テンプレート読み込みと置換
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    html = template.replace("{{ last_update }}", now) \
                   .replace("{{ score }}", str(int(score) if score > 0 else 0)) \
                   .replace("{{ status_msg }}", status_msg) \
                   .replace("{{ advice }}", advice) \
                   .replace("{{ color }}", color) \
                   .replace("{{ table_content }}", table_rows) \
                   .replace("{{ humidity }}", str(humidity)) \
                   .replace("{{ clouds }}", str(clouds))

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def check_weather_and_notify():
    # 実況と予報のベースデータを取得（代表地点：中央地域）
    base_lat = LOCATIONS["杉並中央地域"]["lat"]
    base_lon = LOCATIONS["杉並中央地域"]["lon"]
    
    curr_res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={base_lat}&lon={base_lon}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric").json()
    fore_res = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={base_lat}&lon={base_lon}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric").json()
    
    # Webページ生成
    create_web_page(curr_res, fore_res)

    # LINE通知判定（各地点を巡回）
    alert_needed = False
    rain_keywords = ["Rain", "Snow", "Drizzle", "Thunderstorm"]
    
    for area_name, coords in LOCATIONS.items():
        c_res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric").json()
        if c_res['weather'][0]['main'] in rain_keywords:
            alert_needed = True
            break

    if alert_needed:
        site_url = "https://firstclass-lab.github.io/weather/"
        msg = f"【杉並区・洗濯物アラート】\n雨を検知しました。外干しは危険です！詳細はこちら：\n{site_url}"
        send_line_push(msg)

def send_line_push(message):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    check_weather_and_notify()
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

def create_web_page(report_lines):
    """template.htmlを読み込み、データを流し込んでindex.htmlを作成する"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # カード部分のHTMLを生成
    cards_html = ""
    for line in report_lines:
        area, status = line.split(": ", 1)
        alert_style = "color: #e74c3c; font-weight: bold;" if "雨" in status else "color: #2c3e50;"
        cards_html += f"""
        <div class="card">
            <div class="area-name">{area}</div>
            <div class="status" style="{alert_style}">{status}</div>
        </div>
        """

    # 1. テンプレートファイルを読み込む
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    # 2. 目印（{{ ... }}）を実際のデータに置き換える
    html_content = template.replace("{{ last_update }}", now)
    html_content = html_content.replace("{{ cards }}", cards_html)

    # 3. 最終的な index.html として保存する
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def check_weather_and_notify():
    alert_needed = False
    report_lines = []
    
    for area_name, coords in LOCATIONS.items():
        curr_res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric").json()
        fore_res = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric").json()
        
        curr_status = curr_res['weather'][0]['description']
        fore_status = fore_res['list'][0]['weather'][0]['description']
        
        line = f"{area_name}: 今[{curr_status}] → 3h後[{fore_status}]"
        report_lines.append(line)

        rain_keywords = ["Rain", "Snow", "Drizzle", "Thunderstorm"]
        if curr_res['weather'][0]['main'] in rain_keywords or fore_res['list'][0]['weather'][0]['main'] in rain_keywords:
            alert_needed = True

    create_web_page(report_lines)

    if alert_needed:
        # 新しいユーザー名のURL
        site_url = "https://firstclass-lab.github.io/weather/"
        msg = f"【杉並区・洗濯物アラート】\n雨の予報を検知しました。詳細と今後の推移はこちらで確認してください：\n{site_url}"
        from __main__ import send_line_push
        send_line_push(msg)

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    check_weather_and_notify()
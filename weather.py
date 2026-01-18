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
    """天況を反映したHTMLファイルを作成する"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    adsense_code = ""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>杉並区 洗濯物アラート詳細 | FirstClass Lab</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; text-align: center; padding: 20px; background-color: #f4f7f9; color: #333; }}
            .card {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 20px auto; max-width: 500px; }}
            h1 {{ color: #2c3e50; font-size: 1.5rem; }}
            .status {{ margin: 10px 0; padding: 10px; border-bottom: 1px solid #eee; }}
            .footer {{ font-size: 0.8rem; color: #7f8c8d; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>杉並区 洗濯物監視状況</h1>
        <p>最終更新: {now}</p>
        <div class="card">
            {"".join([f"<div class='status'>{line}</div>" for line in report_lines])}
        </div>
        <div class="card" style="border: 2px dashed #ccc; background: #fafafa;">
            <p style="color: #999;">【広告スペース】</p>
            {adsense_code}
        </div>
        <div class="footer">© 2026 FirstClass Lab</div>
    </body>
    </html>
    """
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
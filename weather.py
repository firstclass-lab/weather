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
    """天況を反映したHTMLファイルを作成する（モダンデザイン版）"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 情報をカード形式のHTMLに変換
    cards_html = ""
    for line in report_lines:
        area, status = line.split(": ", 1)
        # 雨という言葉が入っていたら強調する仕組み（簡易版）
        alert_style = "color: #e74c3c; font-weight: bold;" if "雨" in status else "color: #2c3e50;"
        cards_html += f"""
        <div class="card">
            <div class="area-name">{area}</div>
            <div class="status" style="{alert_style}">{status}</div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>杉並区 洗濯物アラート | FirstClass Lab</title>
        <style>
            :root {{ --main-blue: #007aff; --bg-gradient: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%); }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                background: var(--bg-gradient); 
                color: #333; 
                margin: 0; 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ max-width: 500px; width: 100%; }}
            header {{ text-align: center; margin-bottom: 30px; }}
            h1 {{ font-size: 1.5rem; color: #1e293b; margin-bottom: 8px; }}
            .last-update {{ font-size: 0.85rem; color: #64748b; }}
            
            .card {{ 
                background: rgba(255, 255, 255, 0.9); 
                backdrop-filter: blur(10px);
                border-radius: 20px; 
                padding: 20px; 
                margin-bottom: 15px; 
                box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.5);
                transition: transform 0.2s;
            }}
            .card:hover {{ transform: translateY(-2px); }}
            .area-name {{ font-size: 0.9rem; color: #64748b; margin-bottom: 5px; }}
            .status {{ font-size: 1.1rem; font-weight: 600; }}

            .ad-section {{ 
                margin-top: 20px;
                padding: 40px 20px;
                border: 2px dashed #cbd5e1;
                border-radius: 20px;
                text-align: center;
                color: #94a3b8;
                background: rgba(255,255,255,0.3);
            }}
            footer {{ margin-top: auto; padding: 20px; font-size: 0.8rem; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>杉並区 洗濯物アラート</h1>
                <div class="last-update">最終更新: {now}</div>
            </header>

            {cards_html}

            <div class="ad-section">
                <p>スポンサーリンク</p>
                </div>
        </div>
        <footer>© 2026 FirstClass Lab</footer>
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
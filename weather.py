import os
import requests
from datetime import datetime, timedelta, timezone

# GitHubのSecretsから読み出し
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

LOCATIONS = {
    "杉並中央地域": {"lat": 35.6994, "lon": 139.6364}
}

def create_web_page(curr_data, fore_data):
    """実況データと予報データを解析してHTMLを生成する"""
    # 1. 日本時間の取得
    JST = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
    
    # 2. 現在のデータの抽出
    humidity = curr_data['main']['humidity']
    clouds = curr_data['clouds']['all']
    
    # 3. 3時間後の降水量を取得（存在しない場合は0）
    next_rain = fore_data['list'][0].get('rain', {}).get('3h', 0)

    # 4. 安全スコア計算
    score = 100
    score -= (humidity - 50) * 1.5 if humidity > 50 else 0
    score -= clouds * 0.3
    if next_rain > 0: score = 0 

    # 5. メッセージと色の決定
    if score > 80:
        status_msg, advice, color = "最高の洗濯日和！", "今すぐ干しましょう。夕方までには乾きます。", "#2ecc71"
    elif score > 50:
        status_msg, advice, color = "干せなくはないですが…", "雲が多いか、湿度がやや高めです。", "#f1c40f"
    elif score > 0:
        status_msg, advice, color = "部屋干し推奨", "乾きが遅く、生乾き臭のリスクがあります。", "#e67e22"
    else:
        status_msg, advice, color = "【警告】今すぐ取り込んで！", f"3時間以内に {next_rain}mm の降水予報があります。", "#e74c3c"

    # 6. 時系列テーブルの作成（JST対応 & 降水量表示）
    table_rows = ""
    for item in fore_data['list'][:6]: 
        dt = datetime.fromtimestamp(item['dt'], JST).strftime('%H:%M')
        f_temp = round(item['main']['temp'], 1)
        f_desc = item['weather'][0]['description']
        f_rain = item.get('rain', {}).get('3h', 0)
        f_icon = item['weather'][0]['icon']
        icon_url = f"https://openweathermap.org/img/wn/{f_icon}.png"
        
        # 降水量を表示（0mmでも薄く表示、あれば青文字）
        rain_class = "rain-val" if f_rain > 0 else ""
        rain_info = f"<br><span class='{rain_class}' style='font-size:0.8rem;'>降水:{f_rain}mm</span>"
        
        table_rows += f"<tr><td>{dt}</td><td><img src='{icon_url}' width='30'></td><td>{f_desc}{rain_info}</td><td>{f_temp}℃</td></tr>"

    # 7. template.htmlの読み込みと置換
    # カレントディレクトリのtemplate.htmlを確実に読み込む
    base_path = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_path, "template.html")
    
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    html = template.replace("{{ last_update }}", now) \
                   .replace("{{ score }}", str(int(score))) \
                   .replace("{{ status_msg }}", status_msg) \
                   .replace("{{ advice }}", advice) \
                   .replace("{{ color }}", color) \
                   .replace("{{ table_content }}", table_rows) \
                   .replace("{{ humidity }}", str(humidity)) \
                   .replace("{{ clouds }}", str(clouds))

    # 8. index.htmlの書き出し
    index_path = os.path.join(base_path, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return score

def check_weather_and_notify():
    base = LOCATIONS["杉並中央地域"]
    
    try:
        # APIリクエスト（タイムアウト5秒設定）
        curr_res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={base['lat']}&lon={base['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric", timeout=5).json()
        fore_res = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={base['lat']}&lon={base['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric", timeout=5).json()
        
        if 'main' not in curr_res:
            print("Error: Could not retrieve weather data.")
            return

        # Webページ生成とスコア取得
        current_score = create_web_page(curr_res, fore_res)

        # スコア0（雨）の時だけLINE通知
        if current_score == 0:
            site_url = "https://firstclass-lab.github.io/weather/"
            msg = f"【杉並区・洗濯物アラート】\n雨予報（スコア0点）を検知しました。外干しは避けてください！\n{site_url}"
            send_line_push(msg)
            
    except Exception as e:
        print(f"Runtime Error: {e}")

def send_line_push(message):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("Error: LINE credentials not set.")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload, timeout=5)

if __name__ == "__main__":
    check_weather_and_notify()
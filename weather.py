import os
import requests
from datetime import datetime
import pytz

def get_weather():
    # APIキーと地点設定
    OWM_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    YAHOO_CLIENT_ID = os.environ.get('YAHOO_CLIENT_ID')
    LAT = "35.6994"  # 杉並区天沼
    LON = "139.6364"
    jst = pytz.timezone('Asia/Tokyo')
    
    try:
        # --- 1. Yahoo! API (5分刻みの雨量) ---
        yahoo_url = f"https://map.yahooapis.jp/weather/V1/place?coordinates={LON},{LAT}&appid={YAHOO_CLIENT_ID}&output=json&interval=5"
        y_res = requests.get(yahoo_url).json()
        
        max_rain_nearby = 0.0
        table_5min = ""
        if 'Feature' in y_res:
            weather_list = y_res['Feature'][0]['Property']['WeatherList']['Weather']
            for w in weather_list:
                time_str = f"{w['Date'][-4:-2]}:{w['Date'][-2:]}"
                rain_val = float(w['Rainfall'])
                if rain_val > max_rain_nearby: max_rain_nearby = rain_val
                
                rain_display = f'<span style="color:#3498db;font-weight:bold;">{rain_val}mm</span>' if rain_val > 0 else "0.0mm"
                status_icon = "⚠️雨" if rain_val > 0 else "☁️" # 簡易判定
                table_5min += f"<tr><td>{time_str}</td><td>{status_icon}</td><td>{rain_display}</td></tr>"

        # --- 2. OpenWeatherMap API (実況 & 3時間予報) ---
        curr_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        fore_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        
        curr_res = requests.get(curr_url).json()
        fore_res = requests.get(fore_url).json()

        # 実況データ
        humidity = curr_res['main']['humidity']
        temp = round(curr_res['main']['temp'], 1)
        clouds = curr_res.get('clouds', {}).get('all', 0)
        
        # 3時間予報テーブル生成
        table_3hr = ""
        for f in fore_res['list'][:8]: # 24時間分
            dt_txt = datetime.fromtimestamp(f['dt'], jst).strftime('%H:%M')
            f_temp = round(f['main']['temp'], 1)
            f_hum = f['main']['humidity']
            f_wind = round(f['wind']['speed'], 1)
            f_rain = f.get('rain', {}).get('3h', 0)
            f_icon = "☀️" if f['weather'][0]['main'] == "Clear" else "☁️" if f['weather'][0]['main'] == "Clouds" else "☔"
            table_3hr += f"<tr><td>{dt_txt}</td><td>{f_icon}</td><td>{f_temp}℃/{f_hum}%</td><td>{f_wind}m/s</td><td>{f_rain}mm</td></tr>"

        # --- 3. スコア判定ロジック ---
        base_score = 100
        if humidity > 80: base_score -= 50
        elif humidity > 60: base_score -= 20
        
        status_text = "外干しOK！"
        advice_text = "絶好の洗濯日和です。厚手のものもよく乾きます。"
        
        if max_rain_nearby > 0:
            base_score = 0
            status_text = "今すぐ取り込んで！"
            advice_text = f"【緊急】雨雲レーダーが直近の降雨（最大 {max_rain_nearby}mm/h）を検知しました。"
        elif base_score < 50:
            status_text = "部屋干し推奨"
            advice_text = "湿気が多いか、数時間後に雨の予報があります。"

        score = max(0, min(100, base_score))
        accent_color = "#34d399" if score >= 80 else "#fbbf24" if score >= 50 else "#f87171"

        # --- 4. HTML置換 ---
        with open('template.html', 'r', encoding='utf-8') as f:
            tmpl = f.read()
        
        now = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
        html = tmpl.replace('{{ score }}', str(score)).replace('{{ color }}', accent_color) \
                   .replace('{{ status_msg }}', status_text).replace('{{ advice }}', advice_text) \
                   .replace('{{ humidity }}', str(humidity)).replace('{{ clouds }}', str(clouds)) \
                   .replace('{{ last_update }}', now).replace('{{ table_5min }}', table_5min) \
                   .replace('{{ table_3hr }}', table_3hr).replace('{{ temp }}', str(temp))
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Success: Score {score}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_weather()
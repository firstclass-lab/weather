import os
import requests
from datetime import datetime
import pytz
import traceback

def get_weather():
    OWM_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    YAHOO_CLIENT_ID = os.environ.get('YAHOO_CLIENT_ID')
    LAT, LON = "35.6994", "139.6364"
    jst = pytz.timezone('Asia/Tokyo')
    
    try:
        # --- 1. OpenWeatherMapデータ取得 ---
        curr_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        fore_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        
        curr_res = requests.get(curr_url).json()
        fore_res = requests.get(fore_url).json()

        humidity = curr_res.get('main', {}).get('humidity', 50)
        temp = round(curr_res.get('main', {}).get('temp', 0), 1)
        clouds = curr_res.get('clouds', {}).get('all', 0)

        # --- 2. Yahoo! API (5分刻み) ---
        yahoo_url = f"https://map.yahooapis.jp/weather/V1/place?coordinates={LON},{LAT}&appid={YAHOO_CLIENT_ID}&output=json&interval=5"
        y_res = requests.get(yahoo_url).json()
        
        max_rain_nearby, table_5min = 0.0, ""
        if 'Feature' in y_res:
            for w in y_res['Feature'][0]['Property']['WeatherList']['Weather']:
                time_str = f"{w['Date'][-4:-2]}:{w['Date'][-2:]}"
                rain_val = float(w['Rainfall'])
                if rain_val > max_rain_nearby: max_rain_nearby = rain_val
                rain_display = f'<span style="color:#3498db;font-weight:bold;">{rain_val}mm</span>' if rain_val > 0 else "0.0mm"
                icon_char = "⚠️雨" if rain_val > 0 else ("☀️" if clouds < 30 else "☁️")
                table_5min += f"<tr><td>{time_str}</td><td><span class='weather-icon'>{icon_char}</span></td><td>{rain_display}</td></tr>"

        # --- 3. 3時間予報テーブル (ここが重要) ---
        table_3hr = ""
        forecast_list = fore_res.get('list', [])
        if forecast_list:
            for f in forecast_list[:8]:
                dt_txt = datetime.fromtimestamp(f['dt'], jst).strftime('%H:%M')
                f_main = f.get('main', {})
                f_temp = round(f_main.get('temp', 0), 1)
                f_hum = f_main.get('humidity', 0)
                f_wind = round(f.get('wind', {}).get('speed', 0), 1)
                f_rain = f.get('rain', {}).get('3h', 0) if isinstance(f.get('rain'), dict) else 0
                
                w_main = f.get('weather', [{}])[0].get('main', '')
                icon_char = "☀️" if w_main == "Clear" else "☁️" if w_main == "Clouds" else "☔"
                
                table_3hr += f"<tr><td>{dt_txt}</td><td><span class='weather-icon'>{icon_char}</span></td><td>{f_temp}℃/{f_hum}%</td><td>{f_wind}m/s</td><td>{f_rain}mm</td></tr>"
        else:
            table_3hr = "<tr><td colspan='5'>予報データを取得できませんでした</td></tr>"

        # --- 4. スコア判定 & 置換 ---
        base_score = 100
        if humidity > 80: base_score -= 50
        elif humidity > 60: base_score -= 20
        status_text, advice_text = "外干しOK！", "絶好の洗濯日和です。厚手のものもよく乾きます。"
        if max_rain_nearby > 0:
            base_score = 0
            status_text, advice_text = "今すぐ取り込んで！", f"【緊急】雨雲接近中（最大 {max_rain_nearby}mm/h）"

        score = max(0, min(100, base_score))
        accent_color = "#34d399" if score >= 80 else "#fbbf24" if score >= 50 else "#f87171"

        with open('template.html', 'r', encoding='utf-8') as f:
            tmpl = f.read()
        
        now = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
        # 全ての変数を一気に置換
        html = tmpl.replace('{{ score }}', str(score)) \
                   .replace('{{ color }}', accent_color) \
                   .replace('{{ status_msg }}', status_text) \
                   .replace('{{ advice }}', advice_text) \
                   .replace('{{ humidity }}', str(humidity)) \
                   .replace('{{ clouds }}', str(clouds)) \
                   .replace('{{ last_update }}', now) \
                   .replace('{{ temp }}', str(temp)) \
                   .replace('{{ table_5min }}', table_5min) \
                   .replace('{{ table_3hr }}', table_3hr)
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        print(f"Success: Score {score}")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    get_weather()
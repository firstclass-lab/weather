import os
import requests
from datetime import datetime
import pytz
import traceback
import re

def get_weather():
    OWM_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    YAHOO_CLIENT_ID = os.environ.get('YAHOO_CLIENT_ID')
    LAT, LON = "35.6994", "139.6364"
    jst = pytz.timezone('Asia/Tokyo')
    
    try:
        # --- 1. OWMデータ取得 ---
        curr_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        fore_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        
        curr_res = requests.get(curr_url).json()
        fore_res = requests.get(fore_url).json()

        # 実況データの解析
        humidity = curr_res.get('main', {}).get('humidity', 50)
        temp = round(curr_res.get('main', {}).get('temp', 0), 1)
        clouds = curr_res.get('clouds', {}).get('all', 0)

        # --- 2. 3時間予報の解析（ここが診断ポイント） ---
        table_3hr = ""
        future_rain_risk = 0.0
        forecast_list = fore_res.get('list', [])

        if not forecast_list:
            # データがない場合、APIが返してきたメッセージをそのまま表示
            error_msg = fore_res.get('message', 'No data from API')
            table_3hr = f"<tr><td colspan='5' style='color:red;'>⚠️OWMエラー: {error_msg}</td></tr>"
        else:
            for f in forecast_list[:8]:
                dt_txt = datetime.fromtimestamp(f['dt'], jst).strftime('%H:%M')
                f_main = f.get('main', {})
                f_temp, f_hum = round(f_main.get('temp', 0), 1), f_main.get('humidity', 0)
                f_wind = round(f.get('wind', {}).get('speed', 0), 1)
                f_rain_val = f.get('rain', {}).get('3h', 0) if isinstance(f.get('rain'), dict) else 0
                
                if forecast_list.index(f) < 2 and f_rain_val > 0:
                    future_rain_risk = max(future_rain_risk, f_rain_val)
                
                w_main = f.get('weather', [{}])[0].get('main', '')
                icon_char = "☀️" if w_main == "Clear" else "☁️" if w_main == "Clouds" else "☔"
                table_3hr += f"<tr><td>{dt_txt}</td><td><span class='weather-icon'>{icon_char}</span></td><td>{f_temp}℃/{f_hum}%</td><td>{f_wind}m/s</td><td>{f_rain_val}mm</td></tr>"

        # --- 3. Yahoo! API (5分刻み) ---
        yahoo_url = f"https://map.yahooapis.jp/weather/V1/place?coordinates={LON},{LAT}&appid={YAHOO_CLIENT_ID}&output=json&interval=5"
        y_res = requests.get(yahoo_url).json()
        max_rain_now, table_5min = 0.0, ""
        if 'Feature' in y_res:
            for w in y_res['Feature'][0]['Property']['WeatherList']['Weather']:
                time_str = f"{w['Date'][-4:-2]}:{w['Date'][-2:]}"
                rain_val = float(w['Rainfall'])
                max_rain_now = max(max_rain_now, rain_val)
                icon_char = "⚠️雨" if rain_val > 0 else ("☀️" if clouds < 30 else "☁️")
                table_5min += f"<tr><td>{time_str}</td><td><span class='weather-icon'>{icon_char}</span></td><td>{rain_val}mm</td></tr>"

        # --- 4. スコア判定 ---
        # (以前の強化ロジックを維持)
        if humidity <= 45: base_score = 100
        elif humidity <= 60: base_score = 80
        elif humidity <= 75: base_score = 50
        else: base_score = 20
        if temp < 15: base_score -= 20
        score = 0 if (max_rain_now > 0 or future_rain_risk > 0) else max(0, base_score)
        
        status_text = "外干しOK" if score >= 70 else "部屋干し推奨" if score >= 40 else "外干しNG"
        advice_text = "3時間予報を考慮したアドバイスを表示中"

        # --- 5. 置換と保存 ---
        with open('template.html', 'r', encoding='utf-8') as f:
            tmpl = f.read()
        
        replacements = {
            r'\{\{\s*score\s*\}\}': str(score),
            r'\{\{\s*color\s*\}\}': "#34d399" if score >= 80 else "#fbbf24",
            r'\{\{\s*status_msg\s*\}\}': status_text,
            r'\{\{\s*advice\s*\}\}': advice_text,
            r'\{\{\s*humidity\s*\}\}': str(humidity),
            r'\{\{\s*clouds\s*\}\}': str(clouds),
            r'\{\{\s*last_update\s*\}\}': datetime.now(jst).strftime('%H:%M:%S'),
            r'\{\{\s*temp\s*\}\}': str(temp),
            r'\{\{\s*table_5min\s*\}\}': table_5min,
            r'\{\{\s*table_3hr\s*\}\}': table_3hr
        }

        html = tmpl
        for pattern, value in replacements.items():
            html = re.sub(pattern, value, html)
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Update Success: Score {score}")

    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    get_weather()
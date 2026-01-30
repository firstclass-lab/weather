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
        # --- 1. データ取得 ---
        curr_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        fore_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        
        curr_res = requests.get(curr_url).json()
        fore_res = requests.get(fore_url).json()

        # 実況データ
        humidity = curr_res.get('main', {}).get('humidity', 50)
        temp = round(curr_res.get('main', {}).get('temp', 0), 1)
        clouds = curr_res.get('clouds', {}).get('all', 0)

        # --- 2. Yahoo! API (直近の雨量チェック) ---
        yahoo_url = f"https://map.yahooapis.jp/weather/V1/place?coordinates={LON},{LAT}&appid={YAHOO_CLIENT_ID}&output=json&interval=5"
        y_res = requests.get(yahoo_url).json()
        
        max_rain_now, table_5min = 0.0, ""
        if 'Feature' in y_res:
            for w in y_res['Feature'][0]['Property']['WeatherList']['Weather']:
                time_str = f"{w['Date'][-4:-2]}:{w['Date'][-2:]}"
                rain_val = float(w['Rainfall'])
                if rain_val > max_rain_now: max_rain_now = rain_val
                rain_display = f'<span style="color:#3498db;font-weight:bold;">{rain_val}mm</span>' if rain_val > 0 else "0.0mm"
                icon_char = "⚠️雨" if rain_val > 0 else ("☀️" if clouds < 30 else "☁️")
                table_5min += f"<tr><td>{time_str}</td><td><span class='weather-icon'>{icon_char}</span></td><td>{rain_display}</td></tr>"

        # --- 3. 3時間予報の処理と未来リスクの算出 ---
        table_3hr = ""
        forecast_list = fore_res.get('list', [])
        future_rain_risk = 0.0
        
        if forecast_list:
            for f in forecast_list[:8]: # 24時間分
                dt_txt = datetime.fromtimestamp(f['dt'], jst).strftime('%H:%M')
                f_main = f.get('main', {})
                f_temp, f_hum = round(f_main.get('temp', 0), 1), f_main.get('humidity', 0)
                f_wind = round(f.get('wind', {}).get('speed', 0), 1)
                
                f_rain_val = 0
                if 'rain' in f and isinstance(f['rain'], dict):
                    f_rain_val = f['rain'].get('3h', 0)
                
                # 直近6時間以内に雨予報があるかチェック
                if forecast_list.index(f) < 2 and f_rain_val > 0:
                    if f_rain_val > future_rain_risk: future_rain_risk = f_rain_val
                
                w_main = f.get('weather', [{}])[0].get('main', '')
                icon_char = "☀️" if w_main == "Clear" else "☁️" if w_main == "Clouds" else "☔"
                table_3hr += f"<tr><td>{dt_txt}</td><td><span class='weather-icon'>{icon_char}</span></td><td>{f_temp}℃/{f_hum}%</td><td>{f_wind}m/s</td><td>{f_rain_val}mm</td></tr>"

        # --- 4. 強化版スコア計算ロジック ---
        # A. 湿度によるベーススコア
        if humidity <= 45: base_score = 100
        elif humidity <= 60: base_score = 80
        elif humidity <= 75: base_score = 50
        else: base_score = 20

        # B. 気温による補正（冬場は乾きにくいのでマイナス）
        if temp < 10: base_score -= 20
        elif temp < 15: base_score -= 10

        # C. 雨リスク（実況または予報）
        if max_rain_now > 0 or future_rain_risk > 0:
            score = 0
        else:
            score = max(0, base_score)

        # --- 5. 詳細コメント生成 ---
        if score >= 90:
            status_text = "外干し最強！"
            advice_text = "絶好の洗濯日和です。厚手のタオルやジーンズもパリッと乾きます。"
        elif score >= 70:
            status_text = "外干しOK"
            if temp < 15:
                advice_text = f"気温{temp}℃と低めです。厚手は早めに干し、夕方には取り込みましょう。"
            else:
                advice_text = "標準的な乾き具合です。午後からの湿気上昇に注意してください。"
        elif score >= 40:
            status_text = "部屋干し推奨"
            if humidity > 70:
                advice_text = f"湿度{humidity}%と高めです。外よりも除湿機のある部屋干しが効率的です。"
            else:
                advice_text = "日差しがあっても乾きが遅い日です。薄手のものだけにしましょう。"
        elif score > 0:
            status_text = "半乾き注意"
            advice_text = "気温が低いか湿度が高いです。外に干すと逆に湿気る可能性があります。"
        else:
            status_text = "部屋干し必須"
            if max_rain_now > 0:
                advice_text = f"【注意】雨が降っています。今すぐ部屋に入れましょう。"
            else:
                advice_text = "数時間以内に雨の予報が出ています。今日は部屋干しが安全です。"

        accent_color = "#34d399" if score >= 80 else "#fbbf24" if score >= 50 else "#f87171"

        # --- 6. HTML置換 ---
        with open('template.html', 'r', encoding='utf-8') as f:
            tmpl = f.read()
        
        now = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
        html = tmpl.replace('{{ score }}', str(score)).replace('{{ color }}', accent_color) \
                   .replace('{{ status_msg }}', status_text).replace('{{ advice }}', advice_text) \
                   .replace('{{ humidity }}', str(humidity)).replace('{{ clouds }}', str(clouds)) \
                   .replace('{{ last_update }}', now).replace('{{ temp }}', str(temp)) \
                   .replace('{{ table_5min }}', table_5min).replace('{{ table_3hr }}', table_3hr)
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Success: Update Score {score}")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    get_weather()
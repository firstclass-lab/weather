import os
import requests
from datetime import datetime, timedelta
import pytz

def get_weather():
    # APIキーと地点設定
    OWM_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    YAHOO_CLIENT_ID = os.environ.get('YAHOO_CLIENT_ID')
    LAT = "35.6994"  # 杉並区天沼（杉並中央）
    LON = "139.6364"
    
    try:
        # --- 1. Yahoo! YOLP API で超短期の雨雲チェック ---
        # 5分刻み、1時間後までの降水強度を取得
        yahoo_url = f"https://map.yahooapis.jp/weather/V1/place?coordinates={LON},{LAT}&appid={YAHOO_CLIENT_ID}&output=json&interval=5"
        y_res = requests.get(yahoo_url).json()
        print(f"DEBUG Yahoo Response: {y_res}")        

        # 直近1時間の最大降水強度を確認
        max_rain_nearby = 0.0
        rain_warning_msg = ""
        
        if 'Feature' in y_res:
            weather_data = y_res['Feature'][0]['Property']['WeatherList']['Weather']
            for data in weather_data:
                rain_val = float(data['Rainfall'])
                if rain_val > max_rain_nearby:
                    max_rain_nearby = rain_val
        
        # --- 2. OpenWeatherMap で広域・3時間予報を取得 ---
        curr_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        fore_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        
        curr_res = requests.get(curr_url).json()
        print(f"DEBUG OWM Response: {curr_res}")
        fore_res = requests.get(fore_url).json()

        # スコア算出ロジック
        humidity = curr_res['main']['humidity']
        temp = curr_res['main']['temp']
        base_score = 100
        
        # 湿度による減点
        if humidity > 80: base_score -= 50
        elif humidity > 60: base_score -= 20
        
        # OWMの今後の予報による判定
        future_rain = False
        for f in fore_res['list'][:3]:  # 今後約9時間
            if 'rain' in f or 'snow' in f:
                future_rain = True
                break
        
        if future_rain: base_score -= 60

        # --- 3. 【独自ロジック】Yahoo!の超短期予報を最優先する ---
        max_rain_nearby = 5.0
        status_text = "外干しOK！"
        advice_text = "絶好の洗濯日和です。厚手のものもよく乾きます。"
        
        if max_rain_nearby > 0:
            # 1時間以内に雨雲がある場合、強制的に0点にする
            base_score = 0
            status_text = "今すぐ取り込んで！"
            advice_text = f"【緊急】Yahoo!雨雲レーダーが直近1時間以内の降水（最大 {max_rain_nearby}mm/h）を検知しました。杉並中央地域に雨雲が接近中です。"
        elif base_score < 50:
            status_text = "部屋干し推奨"
            advice_text = "湿気が多いか、数時間後に雨の予報があります。今日は室内が安心です。"

        # スコアの範囲を0-100に制限
        score = max(0, min(100, base_score))

        # HTML生成用のデータ
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
        
        forecast_html = ""
        for f in fore_res['list'][:5]:
            dt = datetime.fromtimestamp(f['dt'], jst).strftime('%H:%M')
            temp_f = f['main']['temp']
            rain_f = f.get('rain', {}).get('3h', 0)
            forecast_html += f"<tr><td>{dt}</td><td>{temp_f}℃</td><td>{rain_f}mm</td></tr>"

        # template.html を読み込んで書き出し
        with open('template.html', 'r', encoding='utf-8') as f:
            tmpl = f.read()
        
        html = tmpl.replace('{{ score }}', str(score))
        html = html.replace('{{ status_msg }}', status_text)
        html = html.replace('{{ advice }}', advice_text)
        html = html.replace('{{ temp }}', str(temp))
        html = html.replace('{{ humidity }}', str(humidity))
        html = html.replace('{{ last_update }}', now)
        html = html.replace('{{ table_content }}', forecast_html)
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        print(f"Update successful: Score {score} (Yahoo! Rain: {max_rain_nearby}mm)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_weather()
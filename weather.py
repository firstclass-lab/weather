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
        yahoo_url = f"https://map.yahooapis.jp/weather/V1/place?coordinates={LON},{LAT}&appid={YAHOO_CLIENT_ID}&output=json&interval=5"
        y_res = requests.get(yahoo_url).json()
        
        max_rain_nearby = 0.0
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
        fore_res = requests.get(fore_url).json()

        # スコア算出ロジック
        humidity = curr_res['main']['humidity']
        temp = curr_res['main']['temp']
        clouds = curr_res.get('clouds', {}).get('all', 0)
        base_score = 100
        
        if humidity > 80: base_score -= 50
        elif humidity > 60: base_score -= 20
        
        future_rain = False
        for f in fore_res['list'][:3]:
            if 'rain' in f or 'snow' in f:
                future_rain = True
                break
        if future_rain: base_score -= 60

        # --- 3. 【独自ロジック】Yahoo!の超短期予報を最優先する ---
        # ★テスト時はここを 5.0 に、本番は 0.0 に戻ったことを確認してください
        # max_rain_nearby = 5.0 
        
        status_text = "外干しOK！"
        advice_text = "絶好の洗濯日和です。厚手のものもよく乾きます。"
        
        if max_rain_nearby > 0:
            base_score = 0
            status_text = "今すぐ取り込んで！"
            advice_text = f"【緊急】Yahoo!雨雲レーダーが直近1時間以内の降雨（最大 {max_rain_nearby}mm/h）を検知しました。"
        elif base_score < 50:
            status_text = "部屋干し推奨"
            advice_text = "湿気が多いか、数時間後に雨の予報があります。"

        score = max(0, min(100, base_score))

        # スコアに応じた色を定義
        if score >= 80:
            accent_color = "#34d399" # 緑
        elif score >= 50:
            accent_color = "#fbbf24" # 黄色
        else:
            accent_color = "#f87171" # 赤

        # 時間とテーブル生成
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
        forecast_html = ""
        for f in fore_res['list'][:5]:
            dt = datetime.fromtimestamp(f['dt'], jst).strftime('%H:%M')
            temp_f = f['main']['temp']
            rain_f = f.get('rain', {}).get('3h', 0)
            forecast_html += f"<tr><td>{dt}</td><td>{temp_f}℃</td><td>{rain_f}mm</td></tr>"

        # --- 4. HTML書き出し処理 ---
        with open('template.html', 'r', encoding='utf-8') as f:
            tmpl = f.read()
        
        # 順番に置換
        html = tmpl.replace('{{ score }}', str(score))
        html = html.replace('{{ color }}', accent_color)
        html = html.replace('{{ status_msg }}', status_text)
        html = html.replace('{{ advice }}', advice_text)
        html = html.replace('{{ humidity }}', str(humidity))
        html = html.replace('{{ clouds }}', str(clouds))
        html = html.replace('{{  clouds  }}', str(clouds))
        html = html.replace('{{ last_update }}', now)
        html = html.replace('{{ table_content }}', forecast_html)
        
        # スペースなし版の保険
        html = html.replace('{{score}}', str(score))
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        print(f"Update successful: Score {score} (Yahoo! Rain: {max_rain_nearby}mm)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_weather()
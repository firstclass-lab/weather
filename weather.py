import os
import requests

# GitHubのSecretsから値を読み出す
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# 杉並区内の3地点
LOCATIONS = {
    "杉並中央地域": {"lat": 35.6994, "lon": 139.6364},
    "杉並北西部":   {"lat": 35.7250, "lon": 139.6010},
    "杉並南部":     {"lat": 35.6800, "lon": 139.6150}
}

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=payload)

def check_weather_and_notify():
    alert_needed = False
    report_lines = []
    
    print("--- 杉並区の「現在」と「予報」を巡回中 ---")
    
    for area_name, coords in LOCATIONS.items():
        # 1. 現在の天気を取得
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric"
        curr_res = requests.get(current_url).json()
        curr_status = curr_res['weather'][0]['description']
        curr_main = curr_res['weather'][0]['main']

        # 2. 3時間予報を取得
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric"
        fore_res = requests.get(forecast_url).json()
        next_f = fore_res['list'][0]
        fore_status = next_f['weather'][0]['description']
        fore_main = next_f['weather'][0]['main']

        # ログ出力用
        line = f"・{area_name}: 今[{curr_status}] → 3h後[{fore_status}]"
        print(line)
        report_lines.append(line)

        # 「今」または「3時間後」のどちらかが雨（雪・雷雨含む）ならアラート対象
        rain_conditions = ["Rain", "Snow", "Drizzle", "Thunderstorm"]
        if curr_main in rain_conditions or fore_main in rain_conditions:
            alert_needed = True

    if alert_needed:
        msg = "【杉並区・洗濯物警戒アラート】\n現在、または3時間以内に雨の予報があります！\n\n" + "\n".join(report_lines)
        send_line_push(msg)
        print(">> 雨を検知。LINEに通知しました。")
    else:
        print(">> 現在および3時間以内に雨の心配はありません。")

if __name__ == "__main__":
    check_weather_and_notify()
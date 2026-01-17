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
    will_rain = False
    details = []
    
    print("--- 杉並区の「3時間予報」をチェック中 ---")
    for area_name, coords in LOCATIONS.items():
        # 「forecast」APIを使用（5日間/3時間ごとの予報）
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric"
        res = requests.get(url).json()
        
        # 直近の予報データ（リストの最初が3時間以内の予報）を取得
        next_forecast = res['list'][0]
        weather_main = next_forecast['weather'][0]['main']
        weather_desc = next_forecast['weather'][0]['description']
        
        print(f"・{area_name}（3時間以内）: {weather_desc}")

        # 雨、雪、霧雨、雷雨を検知
        if weather_main in ["Rain", "Snow", "Drizzle", "Thunderstorm"]:
            will_rain = True
            details.append(f"・{area_name}（予報: {weather_desc}）")

    if will_rain:
        msg = "【杉並区・洗濯物予告アラート】\n3時間以内に雨が降る予報が出ています。今のうちに取り込むか、干すのを控えましょう！\n\n" + "\n".join(details)
        send_line_push(msg)
        print(">> 雨の予報を検知。LINEに通知を送りました。")
    else:
        print(">> 3時間以内に雨の予報はありません。")

if __name__ == "__main__":
    check_weather_and_notify()
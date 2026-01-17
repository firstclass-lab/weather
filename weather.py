import os
import requests

# --- 【修正】環境変数（GitHub Secrets）から読み込む設定 ---
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
    """LINE Messaging APIを使ってプッシュ通知を送る関数"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response

def check_weather_and_notify():
    any_rain = False
    details = []
    
    print("--- 杉並区の天況を巡回中 ---")
    for area_name, coords in LOCATIONS.items():
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&lang=ja&units=metric"
        res = requests.get(url).json()
        
        weather_main = res['weather'][0]['main']
        weather_desc = res['weather'][0]['description']
        print(f"・{area_name}: {weather_desc}")

        # 雨、雪、霧雨、雷雨を検知対象にする
        if weather_main in ["Rain", "Snow", "Drizzle", "Thunderstorm"]:
            any_rain = True
            details.append(f"・{area_name}（{weather_desc}）")

    if any_rain:
        msg = "【杉並区・洗濯物アラート】\n降り始めました！至急取り込んでください。\n\n" + "\n".join(details)
        send_line_push(msg)
        print(">> 降水を検知。LINEに通知を送りました。")
    else:
        # 【テスト用】もし今、雨が降っていなくて、正しくLINEが届くか確認したい場合は、
        # 下の「#」を消して実行してみてください。
        # send_line_push("テスト通知：杉並区は現在晴れています。プログラムは正常です。")
        print(">> 現在、杉並区に降水はありません。")

if __name__ == "__main__":
    check_weather_and_notify()
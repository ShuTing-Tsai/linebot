from flask import Flask, request, abort
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,FollowEvent
)
from dotenv import load_dotenv
import os
from utils import get_titles_by_date

# 初始化
load_dotenv()
app = Flask(__name__)

# Load environment variables
load_dotenv()
channel_access_token = os.getenv('channel_access_token')
channel_secret = os.getenv('channel_secret')

# 如果有一個沒設定，就停止程式並報錯。
if not channel_access_token or not channel_secret:
    raise ValueError("Missing LINE Bot credentials in environment variables")

# 初始化 LINE 機器人的 API 介面及訊息事件處理器。
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# 定義一個根目錄 GET 路由，方便測試你的伺服器是否有跑起來（回傳簡單字串）。
@app.route("/", methods=['GET'])
def home():
    return "Line Bot is running!"

# 定義一個 /callback POST 路由，LINE 官方會把使用者的訊息 POST 到這個網址。
@app.route("/callback", methods=['POST'])
def callback():
    # 從 header 中取得 LINE 傳來的簽章，用來驗證訊息是否合法。
    signature = request.headers['X-Line-Signature']
    # 取得使用者傳來的內容（例如：文字訊息）。
    body = request.get_data(as_text=True)

    # 試圖交由 handler 處理，如果簽章驗證失敗，就中止並回傳 400（Bad Request）。
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 註冊一個函式來處理當使用者傳送文字訊息時的事件。
@handler.add(MessageEvent, message=TextMessage)
# 使用者傳訊息邏輯
def handle_message(event):
    # 取得使用者輸入的訊息內容並去掉前後空白。
    msg = event.message.text.strip()
    # 如果使用者輸入的是範圍（含 ~），則分開起始與結束日期。
    # 否則就視為單一日期。
    try:
        if "~" in msg:
            start, end = msg.split("~")
            result = get_titles_by_date(start.strip(), end.strip())
            if isinstance(result, str):
                # 沒資料的情況，直接回傳文字
                reply = f"🔍 查詢日期：{start.strip()} ～ {end.strip()}\n\n{result}"
            else:
                reply = (
                    f"🗂️ 以下是 {start.strip()} ～ {end.strip()} 之間的公告標題：\n\n"
                    + result
                )
        else:
            date = msg.strip()
            result = get_titles_by_date(date)
            if isinstance(result, str):
                reply = f"📅 查詢日期：{date}\n\n{result}"
            else:
                reply = (
                    f"📅 {date} 的公告標題如下：\n\n"
                    + result
                )
    # 若發生錯誤（例如日期格式錯誤），就告訴使用者請輸入正確格式。
    except Exception:
        result = (
            "😥 抱歉，我沒看懂你輸入的格式！\n\n"
            "請照以下範例輸入日期喔～\n"
            "👉 單日查詢：2025-06-01\n"
            "👉 區間查詢：2025-06-01~2025-06-11"
        )

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))

@handler.add(FollowEvent)
# 新使用者加入時自動發送歡迎訊息
def handle_follow(event):
    welcome_msg = (
        "歡迎來到「衛服部食藥署新聞i報報」！\n\n"
        "請輸入如下格式的日期：\n"
        "例如：\n"
        "👉 2025-06-01（單一天）\n"
        "👉 2025-06-01~2025-06-11（區間）\n\n"
        "我會自動回覆該日期內所有的新聞標題喔～"
    )
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=welcome_msg)
    )


if __name__ == "__main__":
    app.run(port=5000)
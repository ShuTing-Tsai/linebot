from flask import Flask, request, abort
from linebot import WebhookHandler, LineBotApi
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,FollowEvent,
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent
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

# 建立 Flex bubble 列表
def generate_flex_bubbles(entries):
    bubbles = []
    for row in entries.itertuples():
        bubble = BubbleContainer(
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text=str(row.發布日期.date()), weight="bold", size="sm", color="#888888"),
                    TextComponent(text=row.標題, wrap=True, size="md", color="#000000", margin="md")
                ]
            )
        )
        bubbles.append(bubble)
    return bubbles[:10]  # LINE carousel 最多10個 bubble

# 使用者傳訊息的主要處理函式
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    try:
        if "~" in msg:
            start, end = msg.split("~")
            results = get_titles_by_date(start.strip(), end.strip())
            if isinstance(results, str):
                reply = TextSendMessage(text=f"🔍 查詢日期：{start.strip()} ～ {end.strip()}\n\n{results}")
            else:
                bubbles = generate_flex_bubbles(results)
                reply = FlexSendMessage(
                    alt_text=f"{start.strip()}~{end.strip()} 公告標題",
                    contents={
                        "type": "carousel",
                        "contents": [bubble.as_json_dict() for bubble in bubbles]
                    }
                )
        else:
            date = msg.strip()
            results = get_titles_by_date(date)
            if isinstance(results, str):
                reply = TextSendMessage(text=f"📅 查詢日期：{date}\n\n{results}")
            else:
                bubbles = generate_flex_bubbles(results)
                reply = FlexSendMessage(
                    alt_text=f"{date} 公告標題",
                    contents={
                        "type": "carousel",
                        "contents": [bubble.as_json_dict() for bubble in bubbles]
                    }
                )
    except Exception:
        reply = TextSendMessage(
            text=(
                "😥 抱歉，我沒看懂你輸入的格式！\n\n"
                "請照以下範例輸入日期喔～\n"
                "👉 單日查詢：2025-06-01\n"
                "👉 區間查詢：2025-06-01~2025-06-11"
            )
        )

    line_bot_api.reply_message(event.reply_token, reply)

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
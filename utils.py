import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
# from tabulate import tabulate

url = "https://www.fda.gov.tw/DataAction"
headers = {"User-Agent": "Mozilla/5.0"}

# 向網頁發送 GET 請求
res = requests.get(url, headers=headers)

# 把網頁內容轉為文字
soup = BeautifulSoup(res.text, "html.parser")

# 取得頁面純文字（看起來像 JSON）
json_text = soup.get_text()

# 把 JSON 字串轉為 Python 物件
data = json.loads(json_text)

# 轉成 DataFrame
df = pd.DataFrame(data)

# 美化列印前10筆
# print(tabulate(df[["標題", "發布日期"]].head(10), headers='keys', tablefmt='grid', showindex=True))

# 將「發布日期」轉成 datetime 格式，方便用來做日期篩選。
# errors="coerce"：如果轉換失敗，就會變成 NaT（Not a Time）。
df["發布日期"] = pd.to_datetime(df["發布日期"], errors="coerce")

# end_date=None 表示如果沒填結束日期，就查詢單一天的資料。
def get_titles_by_date(start_date, end_date=None):
    # 轉換輸入的日期文字成 datetime 型別
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date) if end_date else start
    # 建立篩選條件：資料中的日期是否落在指定範圍
    # mask 是布林條件，用來篩選「日期落在範圍內」的資料。
    # df.loc[mask] 就是取出符合條件的資料。
    mask = (df["發布日期"] >= start) & (df["發布日期"] <= end)
    results = df.loc[mask]

    if results.empty:
        return "該日期區間沒有發布任何標題。"
    # 把每筆結果組成一行：日期＋標題
    # iterrows() 是逐列取出 DataFrame 的方式。
    return "\n\n".join(f"{row['發布日期'].date()}：{row['標題']}" for _, row in results.iterrows())
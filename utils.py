import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
# from tabulate import tabulate

url = "https://www.fda.gov.tw/DataAction"
headers = {"User-Agent": "Mozilla/5.0"}

res = requests.get(url, headers=headers)

# 把網頁內容轉為文字
soup = BeautifulSoup(res.text, "html.parser")

# 取得頁面純文字（看起來像 JSON）
json_text = soup.get_text()

# 轉成 JSON
data = json.loads(json_text)

# 轉成 DataFrame
df = pd.DataFrame(data)

# 美化列印前10筆
# print(tabulate(df[["標題", "發布日期"]].head(10), headers='keys', tablefmt='grid', showindex=True))

df["發布日期"] = pd.to_datetime(df["發布日期"], errors="coerce")


def get_titles_by_date(start_date, end_date=None):
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date) if end_date else start
    mask = (df["發布日期"] >= start) & (df["發布日期"] <= end)
    results = df.loc[mask]

    if results.empty:
        return "該日期區間沒有發布任何標題。"

    return "\n\n".join(f"{row['發布日期'].date()}：{row['標題']}" for _, row in results.iterrows())
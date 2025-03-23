from google import genai
from google.genai import types
import os
import PIL.Image
import json
import pandas as pd



def invoice_ocr(file_path):
    api_key = os.getenv('gemini_api_key')
    image = PIL.Image.open(f'{file_path}')
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-pro-exp-02-05",
        contents=["你是一個ocr工具，這張圖片是一張收據、發票、報價單，請依你的專業幫我將內容回傳成json格式字串，只要內容不要json與```，其餘部分移除", image]
        # contents=["請幫我擷取這張發票的資料，包括：發票號碼、日期、總金額、賣方、買方（若有）、品項與價格。格式請用 JSON 輸出。",image]
        # contents=["你是一個ocr工具，這張圖片是一張收據、發票、報價單，請依你的專業幫我將內容回傳成方便後續串接系統操作的格式，只要回傳數據內容，其餘移除", image])
    )

    print(response.text)
    try:
        output = response.text.replace('```', '')
        output = output.replace('json', '')
        data = json.loads(output)
    except Exception as e:
        print("解析錯誤：", e)
        data = {}

    if data:
        df = pd.DataFrame([data])
        df = pd.DataFrame(list(data.items()), columns=["Key", "Value"])
        df.to_excel("invoice_data.xlsx", index=False)
        print("已儲存到 invoice_data.xlsx")
    else:
        print("未取得資料")

    return output
from google import genai
from google.genai import types

import PIL.Image



def invoice_ocr(file_path):
    api_key = os.getenv('gemini_api_key')
    image = PIL.Image.open(f'{file_path}')
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-pro-exp-02-05",
        contents=["這張圖片是一張收據、發票、報價單，請依你的智慧幫我將內容回傳成json格式字串，其餘部分移除", image])

    print(response.text)
    return response.text
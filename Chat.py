from openai import OpenAI
from LLMtoHTML import converter
import os

def ask_question_about_text(file_path, question):
    # 1. 讀取文本文件
    with open(file_path, 'r', encoding='utf-8') as f: # 確保使用正確的編碼
            text_content = f.read()
    # 2. 構建提示 (prompt)
    prompt = f"""
    {text_content}

    問題: {question}
    """
    return prompt

def chat_openaiapi():
    client = OpenAI(
        api_key=os.getenv('openai_api_key')
    )

    prompt = ask_question_about_text("./LLMtoHTML.py", "如何修改內容，讓>在代碼部分可以正常顯示而不是&gt;")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        n=1,
        messages=[
            {"role": "system", "content": ""},
            {
                "role": "user",
                "content": "若我的git歷史資料太大包，想把些舊的移除該如何操作比較好 "
            }
        ]
    )


    resp_msg = response.choices[0].message
    print(resp_msg)
    return resp_msg


def chat_gemini():
    client = OpenAI(
        api_key=os.getenv('gemini_api_key'),
        base_url=os.getenv('gemini_api_url')
    )

    prompt = ask_question_about_text("./LLMtoHTML.py", "如何修改內容，讓>在代碼部分可以正常顯示而不是&gt;")

    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        n=1,
        messages=[
            {"role": "system", "content": ""},
            {
                "role": "user",
                "content": """
                幫我寫個Python SHAP (SHapley Additive exPlanations)的範例
                """
            }
        ]
    )


    resp_msg = response.choices[0].message
    print(resp_msg)
    return resp_msg

def chat_groq():
    client = OpenAI(
        api_key=os.getenv('groq_api_key'),
        base_url=os.getenv('groq_api_url')
    )

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        n=1,
        messages=[
            {"role": "system", "content": "使用中文回覆"},
            {
                "role": "user",
                "content": "幫我用Python寫個最基本的CNN代碼"
            }
        ]
    )


    resp_msg = response.choices[0].message
    print(resp_msg)
    return resp_msg


def get_models():
    client = OpenAI(
      api_key=os.getenv('gemini_api_key'),
      base_url=os.getenv('gemini_api_url')
    )

    models = client.models.list()
    # for model in models:
    #  print(model.id)

def third():
    client = OpenAI(
      api_key=os.getenv('gemini_api_key'),
      base_url=os.getenv('gemini_api_url')
    )

    model = client.models.retrieve("gemini-2.0-flash")
    print(model.id)

if __name__=="__main__":
    resp_msg = chat_gemini()
    # resp_msg = chat_groq()
    # resp_msg = chat_openaiapi()
    converter(resp_msg.content)
    # get_models()

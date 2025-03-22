import markdown
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

def llm_to_html(llm_response, format="markdown", filename="output.html"):
    """
    將 LLM 回應轉換為 HTML 檔案，並使用程式碼區塊高亮。
    """
    content = llm_response.text
    if format == "markdown":
        html_content = markdown.markdown(content, extensions=['extra','tables'])

        # 使用 Pygments 高亮程式碼區塊
        def highlight_code(text, language):
            try:
                lexer = get_lexer_by_name(language, stripall=True)
            except:
                lexer = get_lexer_by_name("text", stripall=True)
            formatter = HtmlFormatter(noclasses=True, style="default")
            return pygments.highlight(text, lexer, formatter)

        def replace_code(match):
            code = match.group(2)
            language = match.group(1) if match.group(1) else 'text'
            return f'<div class="codehilite">{highlight_code(code, language)}</div>'

        import re
        
        html_content = html_content.replace('&quot;', '"')
        # html_content = html_content.replace('&qt;', '>')
        # html_content = html_content.replace('&lt;', '<')
        # html_content = html_content.replace('&amp;', '&')
        html_content = re.sub(r'<pre><code class="language-(\w*)">([\s\S]*?)</code></pre>', replace_code, html_content)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>LLM Output</title>
        <style>
        .codehilite {{
            background: #f0f0f0;
            padding: 5px;
            border-radius: 5px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
        }}
        th {{
            padding-top: 12px;
            padding-bottom: 12px;
            text-align: left;
            background-color: #f2f2f2;
            color: black;
        }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

# 範例用法 (假設你有一個 llm_response 物件):
class MockLLMResponse:  # 建立一個模擬的回應物件
    def __init__(self, text):
        self.text = text

def converter(llm_response):
    # Markdown
    llm_response_md = MockLLMResponse(llm_response)
    llm_to_html(llm_response_md, format="markdown", filename="markdown_output.html")

if __name__=="__main__":
    converter(" | Header 1 | Header 2 |\n |----------|----------|\n | Data 1   | Data 2   |\n")

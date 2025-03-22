from flask import Flask, render_template, request, redirect, jsonify, send_from_directory
from flask import session
from flask_session import Session
from datetime import datetime
import os
from markdown import markdown
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import math
import re
import uuid
from utils import speech_to_text, summary
import random
from LLMocr import invoice_ocr


load_dotenv(override=True)
app = Flask(__name__)
# 設定上傳的資料夾路徑
UPLOAD_FOLDER = 'uploads/'
TMP_FOLDER = os.path.join(UPLOAD_FOLDER, 'tmpchunk')

# Configure upload folder
UPLOAD_FOLDER_IMG = 'uploads_img/'
if not os.path.exists(UPLOAD_FOLDER_IMG):
    os.makedirs(UPLOAD_FOLDER_IMG)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TMP_FOLDER'] = TMP_FOLDER
app.config['SECRET_KEY'] = "ASECL"
app.config['SESSION_TYPE'] = "filesystem"

upload_folder = 'uploads'

# 23MB 上限
max_chunk_size = 2 * 1024 * 1024

Session(app)

# 檢查是否有資料夾，沒有則建立
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(TMP_FOLDER):
    os.makedirs(TMP_FOLDER)

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_mock_invoice_text():
    """Generate mock text as if it was extracted from an invoice"""
    invoice_number = f"INV-{random.randint(10000, 99999)}"
    date = datetime.now().strftime("%Y/%m/%d")
    total = round(random.uniform(100, 10000), 2)

    items = [
        {"name": "產品A", "qty": random.randint(1, 5), "price": round(random.uniform(50, 500), 2)},
        {"name": "產品B", "qty": random.randint(1, 3), "price": round(random.uniform(100, 1000), 2)},
        {"name": "產品C", "qty": random.randint(1, 10), "price": round(random.uniform(10, 50), 2)}
    ]

    # Calculate subtotals
    for item in items:
        item["subtotal"] = round(item["qty"] * item["price"], 2)

    # Format the invoice text
    invoice_text = f"""發票號碼: {invoice_number}
日期: {date}
----------------------

項目明細:
"""

    for item in items:
        invoice_text += f"{item['name']} x {item['qty']} @ ${item['price']:.2f} = ${item['subtotal']:.2f}\n"

    invoice_text += f"""
----------------------
小計: ${sum(item['subtotal'] for item in items):.2f}
稅額 (5%): ${sum(item['subtotal'] for item in items) * 0.05:.2f}
總計: ${sum(item['subtotal'] for item in items) * 1.05:.2f}

付款方式: 信用卡
狀態: 已付款

謝謝惠顧!
"""

    return invoice_text


def split_audio(video_path, start_time, end_time, chunk_filename_path):
    '''
    分割儲存音訊檔
    Args:
        原始檔案路徑
        開始時間
        結束時間
        切割後路徑檔名
    '''
    ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=chunk_filename_path)

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")


@app.route("/index2", methods=["GET", "POST"])
def index():
    try:
        # with Groq(api_key=os.getenv('groq_api_key')) as client:
        session_id = session.sid
        transcription = ""
        # summary = ""
        html_content = ""

        if request.method == "POST":
            print("FORM DATA RECEIVED")

            if "file" not in request.files:
                return redirect(request.url)

            file = request.files["file"]
            if file.filename == "":
                return redirect(request.url)

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            if file:
                audio_file= open(file_path, "rb")
                transcription = speech_to_text(audio_file)

                if transcription:
                    msg = summary(transcription)
                    html_content = markdown(msg)
    except Exception as e:
        session_id = e

    finally:
        return render_template('index2.html', transcript=transcription, summary=html_content, session_id=session_id)

@app.route('/autoUpload', methods=['POST'])
def upload_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    audio_file = request.files['audio_file']

    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 設定儲存路徑
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 儲存檔案
    file_path = os.path.join(upload_folder, audio_file.filename)
    audio_file.save(file_path)

    # 取得音訊長度（秒）
    with AudioFileClip(file_path) as audio:
        audio_duration = audio.duration

    file_size = os.path.getsize(file_path)

    # 計算需要分割的片段數量
    num_chunks = math.ceil(file_size / max_chunk_size)

    # 每段的時間長度
    chunk_duration = audio_duration / num_chunks

    combined_text = ''
    formatted_text = ''

    for i in range(num_chunks):
        start_time = int(i * chunk_duration)
        end_time = int((i + 1) * chunk_duration)
        chunk_filename = f"{audio_file.filename[:-4]}_chunk{i}.mp3"
        chunk_file_path = os.path.join(app.config['TMP_FOLDER'], chunk_filename)

        split_audio(file_path, start_time, end_time, chunk_file_path)

        with open(chunk_file_path, "rb") as file:
            client = Groq(api_key=os.getenv('groq_api_key'))
            transcription = client.audio.transcriptions.create(
                file=(chunk_file_path, file.read()),
                model="whisper-large-v3",
                # language="zh",
                language="en",
                # response_format="verbose_json",
                response_format="json"
                # prompt="這裡要轉成的是繁體中文。",
            )
            combined_text += transcription.text + "\n\n"

    formatted_text = re.sub(r'([。！？])', r'\1\n', combined_text)
    print(formatted_text)

    transcription_pth = os.path.join(app.config['TMP_FOLDER'], f'{audio_file.filename[:-4]}.txt')
    with open(transcription_pth, 'w', encoding='utf=8') as output_file:
        output_file.write(formatted_text)

    meeting_summary = summary(formatted_text)
    print(meeting_summary)

    return jsonify({'message': 'Meeting summary completed successfully',
                   'file_path': file_path,
                   'download_url':f'/download/{session.sid}',
                   'summary':markdown(meeting_summary)
                   }), 200

@app.route('/download/<sessiod_id>', methods=['GET'])
def downloadtranscription(sessiod_id):
    return send_from_directory(app.config['TMP_FOLDER'], path=f'{sessiod_id}.txt', as_attachment=True)

@app.route('/fileUpload', methods=['GET','POST'])
def fileUpload():
    if request.method == "GET":
        return render_template('index1.html')

    elif request.method == "POST":
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            file_path = os.path.join(upload_folder, unique_filename)

            # 取得音訊長度（秒）
            with AudioFileClip(file_path) as audio:
                audio_duration = audio.duration

            file_size = os.path.getsize(file_path)

            # 計算需要分割的片段數量
            num_chunks = math.ceil(file_size / max_chunk_size)

            # 每段的時間長度
            chunk_duration = audio_duration / num_chunks

            combined_text = ''
            for i in range(num_chunks):
                start_time = int(i * chunk_duration)
                end_time = int((i + 1) * chunk_duration)
                chunk_filename = f"{unique_filename[:-4]}_chunk{i}.mp3"
                chunk_file_path = os.path.join(app.config['TMP_FOLDER'], chunk_filename)

                split_audio(file_path, start_time, end_time, chunk_file_path)

                with open(chunk_file_path, "rb") as file:
                    client = Groq(api_key=os.getenv('groq_api_key'))
                    transcription = client.audio.transcriptions.create(
                        file=(chunk_file_path, file.read()),
                        model="whisper-large-v3",
                        # language="zh",
                        # response_format="verbose_json",
                        response_format="json"
                        # prompt="這裡要轉成的是繁體中文。",
                    )
                    combined_text += transcription.text + "\n\n"

            meeting_summary = summary(combined_text)
            meeting_summary = markdown(meeting_summary)

            return render_template('index1.html', transcript=combined_text,
                                   summary=meeting_summary)

@app.route('/ocr', methods=['GET','POST'])
def ocr():
    if request.method == "GET":
        return render_template('invoice.html')
    else:
        # Check if an image file was uploaded
        if 'image' not in request.files:
            return "未找到圖片檔案", 400
        file = request.files['image']
        # If the user doesn't select a file
        if file.filename == '':
            return "未選擇檔案", 400
        # If the file is valid
        if file and allowed_file(file.filename):
            # Save the file temporarily (optional)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_FOLDER_IMG, filename)
            file.save(file_path)

            # Generate simulated invoice text
            invoice_text = generate_mock_invoice_text()

            # In a real application, you would process the image here
            invoice_text = invoice_ocr(file_path)

            return invoice_text

    return "不支援的檔案格式", 400



if __name__ == "__main__":
    app.run(debug=True, threaded=True)

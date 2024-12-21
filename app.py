import os
import base64
from flask import Flask, request, render_template, url_for
from yt_dlp import YoutubeDL
import logging
import traceback
import threading

app = Flask(__name__)

# Secret key for session management (ensure it's set in environment variables)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Define the path for downloads
DOWNLOAD_FOLDER = os.path.join('static', 'downloads')

# Create the downloads directory if it doesn't exist
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

def is_valid_youtube_url(url):
    """Validate the YouTube URL format."""
    import re
    youtube_regex = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
    )
    return youtube_regex.match(url)

def download_video(video_url, ydl_opts, result):
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info_dict)
            base, ext = os.path.splitext(filename)
            new_file = base + '.mp3'
            result['link'] = url_for('static', filename='downloads/' + os.path.basename(new_file))
    except Exception as e:
        result['error'] = f"An error occurred: {e}"
        logging.error(f"Error processing video URL {video_url}: {traceback.format_exc()}")

@app.route('/', methods=['GET', 'POST'])
def index():
    link = None
    error = None
    if request.method == 'POST':
        video_url = request.form.get('url')
        if not video_url:
            error = "Please provide a YouTube video URL."
            return render_template('index.html', link=link, error=error)
        
        if not is_valid_youtube_url(video_url):
            error = "Invalid YouTube URL."
            return render_template('index.html', link=link, error=error)
        
        # Prepare yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        # Retrieve and decode the Base64-encoded cookies
        encoded_cookies = os.getenv('YT_DL_COOKIES')
        if encoded_cookies:
            try:
                decoded_cookies = base64.b64decode(encoded_cookies).decode('utf-8')
            except (base64.binascii.Error, UnicodeDecodeError) as e:
                error = "Server configuration error: Invalid cookie encoding."
                logging.error(f"Cookie decoding error: {e}")
                return render_template('index.html', link=link, error=error)

            # Write the decoded cookies to a temporary file
            with open('cookies.txt', 'w', encoding='utf-8') as f:
                f.write(decoded_cookies)
            ydl_opts['cookiefile'] = 'cookies.txt'
        else:
            logging.warning("YT_DL_COOKIES environment variable not set.")
            error = "Server configuration error. Please contact the administrator."
            return render_template('index.html', link=link, error=error)

        # Dictionary to store the result
        result = {}

        # Start the download in a separate thread
        download_thread = threading.Thread(target=download_video, args=(video_url, ydl_opts, result))
        download_thread.start()
        download_thread.join(timeout=100)  # Adjust timeout as needed

        # Clean up the temporary cookies file
        if os.path.exists('cookies.txt'):
            os.remove('cookies.txt')

        if download_thread.is_alive():
            error = "The download process is taking too long. Please try again later."
            logging.error("Download thread timed out.")
            return render_template('index.html', link=link, error=error)

        # Retrieve the result
        link = result.get('link')
        error = result.get('error')

    return render_template('index.html', link=link, error=error)

# Removed app.run() as Render uses Gunicorn

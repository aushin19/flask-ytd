import os

from flask import Flask, request, render_template, url_for
from yt_dlp import YoutubeDL
import logging
import traceback

app = Flask(__name__)

# Secret key for session management (if needed)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Define the path for downloads
DOWNLOAD_FOLDER = os.path.join('static', 'downloads')

# Create the downloads directory if it doesn't exist
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

@app.route('/', methods=['GET', 'POST'])
def index():
    link = None
    error = None
    if request.method == 'POST':
        video_url = request.form.get('url')
        if not video_url:
            error = "Please provide a YouTube video URL."
            return render_template('index.html', link=link, error=error)
        try:
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

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info_dict)
                base, ext = os.path.splitext(filename)
                new_file = base + '.mp3'
                link = url_for('static', filename='downloads/' + os.path.basename(new_file))
        except Exception as e:
            error = f"An error occurred: {e}"
            logging.error(f"Error processing video URL {video_url}: {traceback.format_exc()}")
    return render_template('index.html', link=link, error=error)

if __name__ == '__main__':
    app.run(debug=False)

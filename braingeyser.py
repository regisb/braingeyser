#! /usr/bin/env python

import argparse
import os

import chardet
from flask import Flask, render_template, redirect, url_for, send_from_directory
import pycaption

app = Flask(__name__)

# TODO
# - Convert mkv videos to mp4: avconv -i file.mkv -vcodec copy -acodec mp3 file.mp4
# - Convert srt files to vtt? (not sure it's necessary)

class Videos:
    ROOT_DIR = os.environ.get('VIDEO_ROOT_DIR', '/tmp')
    SUPPORTED_EXTENSIONS = ['.mp4', '.avi']
    SUPPORTED_SUBTITLES_EXTENSIONS = ['.srt', '.vtt']


@app.route('/')
def home():
    return redirect(url_for('navigate', root=''))


@app.route('/navigate/')
@app.route('/navigate/<path:root>')
def navigate(root=''):
    absolute_root = os.path.join(Videos.ROOT_DIR, root)
    directories = []
    videos = []
    for path in sorted(os.listdir(absolute_root)):
        absolute_path = os.path.join(absolute_root, path)
        relative_path = os.path.join(root, path)
        if os.path.isdir(absolute_path):
            directories.append({
                'name': path,
                'path': relative_path
            })
        elif path[-4:] in Videos.SUPPORTED_EXTENSIONS:
            videos.append({
                'name': path,
                'path': relative_path
            })
    return render_template('navigate.html', directories=directories, videos=videos)

@app.route('/video/<path:src>')
def video(src):
    root = os.path.dirname(src)
    absolute_root = os.path.join(Videos.ROOT_DIR, root)
    target = {
        'name': os.path.basename(src),
        'path': src,
    }

    # Find subtitles
    # (we don't use glob because it does not work with '[' characters in the path name)
    subtitles = []
    video_name = os.path.splitext(os.path.basename(src))[0]
    for subtitle in sorted(os.listdir(absolute_root)):
        subtitle_name, subtitle_ext = os.path.splitext(subtitle)
        if subtitle_ext not in Videos.SUPPORTED_SUBTITLES_EXTENSIONS:
            continue
        subtitle_name = os.path.basename(subtitle)
        is_default = video_name in subtitle_name
        subtitles.append({
            'name': subtitle_name,
            'path': os.path.join(root, subtitle_name),
            'default': is_default,
        })

    return render_template('video.html', video=target, subtitles=subtitles)

@app.route('/data/<path:src>')
def data(src):
    # Surprisingly, Flask handles mp4 file streaming magnificently. So we don't
    # need to setup nginx for mp4 file streaming.
    directory = os.path.join(Videos.ROOT_DIR, os.path.dirname(src))
    filename = os.path.basename(src)
    return send_from_directory(directory, filename)

@app.route('/track/<path:src>')
def track(src):
    return convert_to_vtt(os.path.join(Videos.ROOT_DIR, src))

def convert_to_vtt(path):
    """
    Convert a subtitles file from any format (e.g: srt) to vtt. This is
    necessary for use with videojs, which supports only vtt subtitles.
    """
    caps = open(path, 'rb').read()
    try:
        caps = caps.decode('utf8')
    except UnicodeDecodeError:
        # Attempt to read with custom encoding
        detected = chardet.detect(caps)
        caps = caps.decode(detected['encoding'])

    caps = caps.strip("\ufeff").strip("\n").strip("\r")
    sub_reader = pycaption.detect_format(caps)
    if sub_reader is None:
        return None
    if sub_reader != pycaption.WebVTTReader:
        read_caps = sub_reader().read(caps)
        caps = pycaption.WebVTTWriter().write(read_caps)
    return caps

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A video streaming server")
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=8000)
    parser.add_argument('path', help='Source directory of video files')
    args = parser.parse_args()

    Videos.ROOT_DIR = os.path.abspath(args.path)
    app.run(host=args.host, port=args.port, debug=True)

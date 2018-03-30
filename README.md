# Braingeyser

A lightweight HTTP video streamer.

![](https://cdn.pucatrade.com/cards/crops/sm/2116.jpg)


## Install

Python 3 is required. Install requirements with:

    pip install -r requirements.txt

## Usage

In development:

    ./braingeyser.py /path/to/my/video/folder

In production:

    VIDEO_ROOT_DIR=/path/to/my/video/folder gunicorn app:app

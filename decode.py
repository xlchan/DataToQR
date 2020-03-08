import base64
import json
import os
from logging import info

from cv2 import VideoCapture
from numpy import ndarray
from pyzbar.pyzbar import decode, Decoded
from tqdm import tqdm

from constants import FIRST_DELIMITER, format, SECOND_DELIMITER


def extract_video(video_path: str) -> str:
    prefix = "[Decode Video] "
    
    # Setup
    info(prefix + "Setup execution")
    
    video = VideoCapture(video_path)
    data = ""
    frames = []
    success = True
    
    image_array: ndarray
    
    info(prefix + "Collecting video frames")
    while success:
        success, image_array = video.read()
        
        if success:
            # Add frames to list
            frames.append(image_array)
    
    for image_array in tqdm(frames, desc=prefix + "Decoding frames"):  # type: ndarray
        image_decoded: Decoded
        
        # Decode video
        image_decoded = decode(image_array)[0]
        data += image_decoded.data.decode("utf-8")
    
    return data


def write_data(data: str):
    for datas in data[:-1].split(FIRST_DELIMITER):
        raw_information, raw_data = datas.split(SECOND_DELIMITER)
        # information
        json_information = base64.b64decode(raw_information).decode("utf-8")
        information = json.loads(json_information)
        # data
        encoded_data = base64.b64decode(raw_data).decode("utf-8")
        
        path = information[format["path"]]
        encoding = information[format["encoding"]]
        folder_path = os.path.dirname(path)
        
        os.makedirs(folder_path, exist_ok=True)
        
        with open(path, "w", encoding=encoding) as file:
            file.write(encoded_data)

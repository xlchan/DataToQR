import base64
import json
import logging
import os
from multiprocessing import freeze_support, Pool
from typing import Optional

import cv2
from pyzbar.pyzbar import decode, Decoded
from tqdm import tqdm

from constants import FIRST_DELIMITER, format, SECOND_DELIMITER

# Logging
logging.root.setLevel(logging.NOTSET)

"""
# Doesn`t work. See extract_video multiline comment at the bottom
def _extract_video__handle_thread(current_data: Tuple[int, np.ndarray, np.array]):
    "\""Inserts the image data at the specific index"\""
    index, data, data_array = current_data
    
    data_array[index] = decode(data)[0].data.decode("utf-8")"""


def _write_video__write__handle_thread(passed: tuple):
    """Writes the file. Thread handler for write_video"""
    data: str
    delimiter: str
    
    unsplitted_data, delimiter = passed
    
    # -<()>- # Extract data # -<()>- #
    raw_information, raw_data = unsplitted_data.split(delimiter)
    
    information = json.loads(
        base64.b64decode(raw_information).decode("utf-8")
    )
    data = base64.b64decode(raw_data).decode("utf-8")
    
    # -<()>- # Get information # -<()>- #
    path = information[format["path"]]
    encoding = information[format["encoding"]]
    folder_path = os.path.dirname(path)
    
    # Get kwargs
    kwargs = {}
    if encoding:
        kwargs["encoding"] = encoding
    
    # -<()>- # Create file # -<()>- #
    
    os.makedirs(folder_path, exist_ok=True)
    
    with open(path, "w", **kwargs) as file:
        file.write(data)


class Decoder:
    @staticmethod
    def build_message(msg: str) -> str:
        """
        Builds the complete message.
        
        :param msg: The message
        :type msg: str
        
        :return: New, built message
        :rtype: str
        """
        return "[Decode Video] " + msg
    
    @staticmethod
    def extract_video(
            video_path: str,
            threads: Optional[int] = None
    ):
        """
        Extracts the data from a given video.
        
        :param video_path: The path to the video
        :type video_path: str
        
        :param threads: How many threads should be used. Currently unavailable. Will be add in the future. If None,
        default value will be chosen. default: `os.cpu_count()`
        :type threads: int, None
        
        :return: data
        :rtype: str
        """
        # Setup
        threads = threads or os.cpu_count()
        
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frames = []
        data = []
        
        # Collecting video frames
        for _ in tqdm(range(frame_count), total=frame_count, desc=Decoder.build_message("Collecting video frames")):
            image_array = cap.read()[1]
            
            frames.append(image_array)
        
        for image_array in tqdm(frames, desc=Decoder.build_message("Decoding frames")):
            decoded_image: Decoded
            decoded_image = decode(image_array)[0]
            
            data.append(decoded_image.data.decode("utf-8"))
        
        return "".join(data)
        
        """
        # If someone know how to get this working, please let me know
        
        data_array = Manager().list([""]) * frame_count
        
        with Pool(threads) as pool:
            # Saving index and data to pass it to the thread handler.
            # Saving data_array to access it in the the thread handler
            pool_data = [[i, value, data_array] for i, value in enumerate(frames)]
            
            list(
                tqdm(
                    pool.imap(_extract_video__handle_thread, pool_data),
                    total=len(pool_data),
                    desc=self.build_message("Decoding QR-Codes")
                )
            )
        
        return "".join(data_array)"""
    
    @staticmethod
    def write_files(
            data: str,
            first_delimiter: str = FIRST_DELIMITER,
            second_delimiter: str = SECOND_DELIMITER,
            threads: Optional[int] = None
    ):
        """
        Writes files from the given data.
        
        :param data: The data
        :type data: str
        
        :param first_delimiter: The delimiter that should be used as first_delimiter for the data
        :type first_delimiter: str
        
        :param second_delimiter: The delimiter that should be used as second_delimiter for the data
        :type second_delimiter: str
        
        :param threads: How many threads should be used. If None, default value will be chosen. default:
        `os.cpu_count()`
        :type threads: int, None
        """
        
        # Setup
        threads = threads or os.cpu_count()
        
        data_list = data[:-1].split(FIRST_DELIMITER)
        pool_data = [
            [data, second_delimiter] for data in data_list
        ]
        
        with Pool(threads) as pool:
            freeze_support()
            
            list(
                tqdm(
                    pool.imap(_write_video__write__handle_thread, pool_data),
                    total=len(pool_data),
                    desc=Decoder.build_message("Writing files")
                )
            )
            
            pool.close()
            pool.join()

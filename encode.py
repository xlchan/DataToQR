import os
import shutil
import string
import subprocess
import tempfile
from logging import info
from multiprocessing import freeze_support, Pool
from typing import List, Optional

import magic
import qrcode
from PIL import ImageFile
from tqdm import tqdm

from classes import File
from constants import FIRST_DELIMITER, SECOND_DELIMITER
from utils import abs_path

mime = magic.Magic(mime=True)


class Data:
    class Default:
        length = 27
        prefix = "---"
        choices = string.digits + string.ascii_letters
    
    @staticmethod
    def get_data(files: List[File]) -> str:
        return "".join([
            f"{file.get_information()}{SECOND_DELIMITER}{file.get_data()}{FIRST_DELIMITER}"
            for file in files
        ])
    
    @staticmethod
    def get_data_from_text(
            path: str,
            file_encoding: str = "utf-8",
            *_, **__
    ) -> File:
        """
        Default function to get data from a file.
        Reads the file and encodes it into base64.
        
        :param path: The path of the file
        :type path: str
        
        :param file_encoding: The encoding the file is saved in.
            default: "utf-8"
        :type file_encoding: str
        
        :param _: Ignore
        :param __: Ignore
        
        :return: Two values:
            0: The encoded data
            1: The information for the data
        :rtype: tuple
        """
        
        # Data
        with open(path, "r", encoding=file_encoding) as file:
            data = file.read()
        
        return File(
            path=path,
            data=data,
            encoding=file_encoding
        )
    
    @staticmethod
    def get_data_from_folder(
            folder_path: str,
            mime_type_functions: Optional[dict] = None,
            recursive: bool = True,
            *args, **kwargs
    ) -> list:
        """
        Creates data for all files in a folder (and subfolders, if `recursive` is True)
        
        :param folder_path: The path of the folder
        :type folder_path: str
        
        :param mime_type_functions: A dictionary that specifies what function should be used, for special mimetypes.
        The dictionary must follow this scheme:
            key => the mimetype (lowercase)
            value => the function
        
        The function takes these arguments:
            file = The absolute path of the current file
            *args = *args passed to this (get_data_from_folder) function
            **kwargs = **kwargs passed to this (get_data_from_folder) function
        
        This field is optional.
        If a function for a mimetype couldn`t be found whether by the default functions nor in the mime_type_functions,
        a ValueError will be raised.
        :type mime_type_functions: dict, None
        
        :param recursive: Whether all subfolders should also be handled
        :type recursive: bool
        
        :param args: *args that get`s passed to the data functions
        :param kwargs: **kwargs that get`s passed to the data functions
        
        :return: list containing all data using default scheme
        :rtype: list
        
        :exception:
            ValueError:
                If a function for a mimetype couldn`t be found (either by the default functions or by the
                mime_type_functions functions), a ValueError will occur.
        """
        datas = []
        
        # Iterate through all files and folders in folder
        for _file in os.listdir(folder_path):  # type: str
            file = abs_path(folder_path, _file)
            
            # If folder was found and recursive is True do THIS function again
            if recursive and os.path.isdir(file):
                datas.extend(Data.get_data_from_folder(
                    folder_path=file,
                    mime_type_functions=mime_type_functions,
                    recursive=recursive,  # Weird pass but good practice
                    *args, **kwargs
                ))
                continue
            
            mime_type = mime.from_file(file)
            # If mime_type_functions is defined and the mimetype is in it, use it`s function
            if mime_type_functions and mime_type in mime_type_functions.keys():
                func = mime_type_functions[mime_type]
            else:
                first = mime_type.split("/")[0]
                func = getattr(Data, f"get_data_from_{first}", Data.get_data_from_text)
            
            datas.append(func(file, *args, **kwargs))
        
        return datas


def handle_thread(x: list):
    Encoder.create_frame(x[0], x[1])


class Encoder:
    @staticmethod
    def create_frame(
            data: str,
            output_path: str = "image.png"
    ):
        """
        Creates a QR-Code image of the given `data` and saves it in the `output_path`.
        
        :param data: The data
        :type data: str
        
        :param output_path: The path where the file should be saved
        :type output_path: str
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            border=0,
            box_size=3
        )
        qr.add_data(data)
        
        img = qr.make_image()  # type: ImageFile
        
        img.save(output_path)
    
    @staticmethod
    def create_video(
            data: str,
            piece_size: int = 2900,
            output_video_path: Optional[str] = None,
            
            temp_folder: Optional[str] = None,
            skip_temp: bool = True,
            delete_tmp: bool = True,
            
            ffmpeg_location: str = "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
            video_args: Optional[dict] = None,
            timeout: int = 500,
            
            threads: Optional[int] = None
    ):
        """
        Creates a video from the given `data` and saves it in the `output_video_path`.
        The data will be splitten into smaller pieces (define the length by setting `piece_size`).
        The frames will be saved in a `temp_folder` and then put together using ffmpeg. Custom args for ffmpeg can be
        defined by defining `video_args`.
        
        :param data: The data
        :type data: str
        
        :param piece_size: The size of the single pieces of the splitted data
        :type piece_size: int
        
        :param output_video_path: The path where the video should be saved
        :type output_video_path: str, None
        
        :param temp_folder: Absolute path to the temporary folder where the images should be saved. If None,
        default value will be used. default: `tempfile.gettempdir()`
        :type temp_folder: str, None
        
        :param skip_temp: If True, images found in the `temp_folder` will be skipped. While creating the single
        images of the data, it`ll be checked if the current index already exists. E.g.: The temp folder contains
        images from number 0 to 6. So the first seven images will be skipped.
        It won`t be checked, whether the data in the found temp images is the actual data.
        !Actual unavailable!
        :type skip_temp: bool
        
        :param delete_tmp: Whether the `temp_folder` should be deleted after the video got created.
        :type delete_tmp: bool
        
        :param ffmpeg_location: The location of ffmpeg.
        :type ffmpeg_location: str
        
        :param video_args: Extra arguments for ffmpeg. If None, default value will be used. default: {
            "-framerate", "24",
            "-b:v", "1M",
        }
        :type video_args: dict, none
        
        :param timeout: Timeout for ffmpeg.
        :type timeout: int
        
        :param threads: How many threads should be used. If None, default value will be chosen. default:
        `os.cpu_count()`
        :type threads: int, None
        """
        img: str
        
        video_args = video_args or [
            "-framerate", "24",
            "-b:v", "1M",
        ]
        temp_folder = temp_folder or tempfile.gettempdir()
        output_video_path = output_video_path or p(os.getcwd(), "qr_data.avi")
        threads = threads or os.cpu_count()
        prefix = "[Create Video] "
        
        # Setup
        info(prefix + "Setup execution")
        
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)
        
        # Splitting data
        datas = [data[i:i + piece_size] for i in range(0, len(data), piece_size)]
        
        # Skip data
        # Will be added
        
        count = len(str(len(datas)))
        # Create QR Codes
        info(prefix + "QR-Codes get`s generated")
        pool_data = [
            (single_data, abs_path(temp_folder, "image{0:0=" + str(count) + "d}.png").format(i))
            for i, single_data in enumerate(datas)
        ]
        
        with Pool(threads) as pool:
            freeze_support()
            list(
                tqdm(
                    pool.imap(handle_thread, pool_data), total=len(pool_data), desc="Generating QR-Codes"
                )
            )
            
            pool.close()
            pool.join()
        
        # Create Video
        info(prefix + "Video get`s created")
        
        process = subprocess.Popen([
            ffmpeg_location,
            "-i", abs_path(temp_folder, "image%" + str(count).zfill(2) + "d.png"),
            *video_args,
            output_video_path
        ])
        
        if delete_tmp:
            process.wait(timeout)
            shutil.rmtree(temp_folder)

import os
import shutil
import string
import subprocess
import tempfile
from logging import info
from typing import List, Optional

import magic
import qrcode
from PIL import ImageFile
from tqdm import tqdm

from classes import File
from constants import FIRST_DELIMITER, SECOND_DELIMITER

mime = magic.Magic(mime=True)


def p(*args: str) -> str:
    return os.path.abspath(os.path.join(*args))


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
    def get_b64_data(
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
            # Get absolute path
            file = p(folder_path, _file)
            
            # If folder was found and recursive is True do THIS function again
            if recursive and os.path.isdir(file):
                # Folder code
                datas.extend(Data.get_data_from_folder(
                    folder_path=file,
                    mime_type_functions=mime_type_functions,
                    recursive=recursive,  # Weird pass but good practice
                    *args, **kwargs
                ))
                continue
            
            # File code
            mime_type = mime.from_file(file)
            
            # Get func
            func = None
            
            # If mime_type_functions is defined and the mimetype is in it, use it`s function
            if mime_type_functions and mime_type in mime_type_functions.keys():
                func = mime_type_functions[mime_type]
            else:
                func = Data.get_b64_data
            
            datas.append(func(file, *args, **kwargs))
        
        return datas


def create_frame(data: str, output_path: str = "image.png"):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        border=0,
        box_size=3
    )
    qr.add_data(data)
    
    img = qr.make_image()  # type: ImageFile
    
    img.save(output_path)


def create_video(
        data: str,
        temp_folder: Optional[str] = None,
        split_character: int = 2900,
        output_video_path: Optional[str] = None,
        video_args: Optional[dict] = None,
        skip_temp: bool = True,
        ffmpeg_location: str = "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
        delete_tmp: bool = True,
        timeout: int = 500
):
    img: str
    
    video_args = video_args or [
        "-framerate", "24",
        "-b:v", "1M",
    ]
    temp_folder = temp_folder or tempfile.gettempdir()
    output_video_path = output_video_path or p(os.getcwd(), "qr_data.avi")
    prefix = "[Create Video] "
    
    # Setup
    info(prefix + "Setup execution")
    
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)
    
    # Splitting data
    datas = [data[i:i + split_character] for i in range(0, len(data), split_character)]
    
    # Skip data
    # Will be added
    
    count = len(str(len(datas)))
    # Create QR Codes
    info(prefix + "QR-Codes get`s generated")
    for i, single_data in enumerate(tqdm(datas, desc="Generating QR-Codes")):
        create_frame(single_data, p(temp_folder, "image{0:0=" + str(count) + "d}.png").format(i))
    
    # Create Video
    info(prefix + "Video get`s created")
    
    process = subprocess.Popen([
        ffmpeg_location,
        "-i", p(temp_folder, "image%" + str(count).zfill(2) + "d.png"),
        *video_args,
        output_video_path
    ])
    
    if delete_tmp:
        process.wait(timeout)
        shutil.rmtree(temp_folder)

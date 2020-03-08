import os

CURRENT = os.getcwd()


def path(*args: str) -> str:
    return os.path.abspath(os.path.join(*args))


from decode import extract_video, write_data

data = extract_video(path(CURRENT, "video.avi"))
write_data(data)

"""
from encode import Data, create_video

folder_data = Data.get_data_from_folder(path(CURRENT, "Test"))
data = Data.get_data(folder_data)

create_video(temp_folder=path(CURRENT, "tmp"), output_video_path=path(CURRENT, "video.avi"), data=data)"""

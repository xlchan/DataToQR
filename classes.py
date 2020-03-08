import base64
import json
from typing import Union

from constants import format


class File:
    def __init__(self, path: str, data: str, encoding: str):
        self.path = path
        self.data = data
        self.encoding = encoding
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} object {self.path=} {self.data[:20]=} {self.encoding=}>"
    
    @property
    def information(self) -> dict:
        """Returns information about this file"""
        return {
            format["path"]: self.path,
            format["encoding"]: self.encoding
        }
    
    @property
    def json_information(self) -> str:
        return json.dumps(self.information, separators=(',', ':'))
    
    def get_data(self):
        return self.encode_data(self.data)
    
    def get_information(self):
        return self.encode_data(self.json_information)
    
    @staticmethod
    def encode_data(data: Union[bytes, str]) -> str:
        if type(data) is str:
            return base64.b64encode(bytes(data, encoding="utf-8")).decode("utf-8")
        return base64.b64encode(data)
    
    @staticmethod
    def decode_data(data: Union[bytes, str]) -> str:
        return base64.b64decode(data)

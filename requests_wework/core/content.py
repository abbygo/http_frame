import os

import yaml

from requests_wework.core.exceptions import FileNotFound


class Content:
    def __init__(self, path):
        # 判断传入的是否是文件
        if not os.path.isfile(path):
            raise FileNotFound(f"{path} not file")
        # 切换文件路径，获取后置并且全部转化为小写
        file_suffix = os.path.splitext(path)[1].lower()
        # 判断后置是否在列表里面
        if file_suffix in [".yaml", ".yml"]:
            self.path = path
            with open(path,encoding='utf-8') as f:
                self._data = yaml.safe_load(f)
            # todo
            self._filepath, self._tmpfilename = os.path.split(path)
    # 获取数据
    def get_data(self):
        return self._data


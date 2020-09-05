import importlib

import re
import time

import types

from string import Template
from typing import Union, Dict

import yaml
from loguru import logger

from requests_wework.core.content import Content
from requests_wework.core.exceptions import ValidationFailure
from requests_wework.core.models import TestCase
from requests_wework.core.parser import build_url
from requests_wework.core.response import ResponseObject
from requests_wework.ExtFiles2Case import utils


def duration_run_time(fun):
    """
    持续运行时间
    :param fun:
    :return:
    """

    def wrapper(*args, **kargs):
        start_time = time.time()
        result = fun(*args, **kargs)
        # 保留2位小数
        duration_time = format(time.time() - start_time, ".2f")
        logger.info(f"duration_run_time:{duration_time}s")
        return result

    return wrapper


class BaseAction:
    # 依赖
    depends = []
    # 局部函数表，key是函数名，value 是包含这个函数的类名地址
    local_variable = {}

    # 变量名说明
    # yaml_data(yaml中的数据)--》yaml 中的最外层key,value：request_key(dict_key),request_value（dict_value）,
    # -->yaml 第2层中的字典key request_entry_key(dict_key); request_entry_value((dict_value))

    def __init__(self, content: Union[Content, Dict]):
        """
        1、得到需要的数据
        :param content: 获取数据的类
        """
        if isinstance(content, Content):
            self.yaml_data: dict = content.get_data()
        else:
            self.yaml_data: dict = content

        self.parse_content()

    def parse_content(self):
        """
        1、导入依赖
        2、寻找以def开头的测试用例，得到真实的姓名，提供给虚拟类中fun_name
        3、创建虚拟类（用于运行用例）--》这个类中有2个变量储存了用例名（eg:gettoken），
        用例值
        eg:
        "run_request": {
            "method": "GET",
            "url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            "params": {
                "corpid": "wwf2dbb0a93f2eac33"
            },
            "headers": {
                "User-Agent": "python-requests/2.24.0",
            },
            "validate": [
                {
                    "eq": [
                        "status_code",
                        200
                    ]
                })
           a:动态创建class, 在回调函数中传入方法run和init,并没有调用类
            tmp_class = types.new_class(
                "tmp_class", (), {}, lambda ns: ns.update(cls_dict)
            )
            b: 实例化类，把用例数据存放到变量中；在把类名地址存在字变量列表中
            self.local_variable[request_key] = tmp_class(request_value, request_key)
        :return: 
        """
        for request_key, request_value in self.yaml_data.items():
            if "depend" == request_key:
                # 循环导入
                for depend in request_value:
                    self.depends.append(importlib.import_module(depend))
            # 函数的命名规则都要一个前缀来表示是函数，test_
            elif request_key.startswith("test_"):
                #   tmp_class  类的初始化 方法
                def __init__(s, request_value, request_key):
                    s.request_key = request_key
                    s.request_value = request_value

                # tmp_class 的方法
                def run(s, testcase_obj: TestCase = None):
                    """
                    
                    :param s: 
                    :param testcase_obj: 测试对象
                    :return: 
                    """
                    for (
                        request_entry_key,
                        request_entry_value,
                    ) in s.request_value.items():
                        # 判断方法名的前置是run_
                        if request_entry_key.startswith("run_"):
                            # 切割列表得到真实的方法名
                            request_method_name = request_entry_key[4:]
                            if self.local_variable.get(request_method_name):
                                # 这句代码暂时不会执行，
                                return self.local_variable[request_method_name].run()
                            else:
                                for import_mod in self.depends:
                                    # 判断导入的模块中是否包含属性或方法
                                    if hasattr(import_mod, request_method_name):
                                        request_dict = self.parse_value(
                                            request_entry_value, testcase_obj
                                        )

                                        # 这句代码实际就是调用是发送请求的地方
                                        return self.send(
                                            request_dict,
                                            import_mod,
                                            request_method_name,
                                            testcase_obj,
                                        )


                def init_tmp_class():
                    cls_dict = {"__init__": __init__, "run": run}
                    # 动态创建class, 在回调函数中传入方法run和init,并没有调用类
                    tmp_class = types.new_class(
                        "tmp_class", (), {}, lambda ns: ns.update(cls_dict)
                    )
                    # 把方法名作为key,类地址作为value存入字典--》eg:<class 'dict'>: {'get_token': <types.tmp_class object at 0x0552E388>}
                    # 实例化类
                    self.local_variable[request_key] = tmp_class(request_value, request_key)

                init_tmp_class()

    # 日志
    def log_req_resp_details(self, url, method, request_dict, res):
        err_msg = "\n{} DETAILED REQUEST & RESPONSE {}\n".format("*" * 32, "*" * 32)

        # log request
        err_msg += "====== request details ======\n"
        err_msg += f"url: {url}\n"
        err_msg += f"method: {method}\n"
        headers = request_dict.pop("headers", {})
        err_msg += f"headers: {headers}\n"
        for k, v in request_dict.items():
            v = utils.omit_long_data(v)
            err_msg += f"{k}: {repr(v)}\n"

        err_msg += "\n"

        # log response
        err_msg += "====== response details ======\n"
        err_msg += f"status_code: {res.status_code}\n"
        err_msg += f"headers: {res.headers}\n"
        err_msg += f"body: {repr(res.text)}\n"
        logger.error(err_msg)

    @duration_run_time
    def send(
        self,
        request_dict: dict,
        import_mod,
        request_method_name,
        testcase_obj: TestCase = None,
    ):
        """
        发送请求入口
        :param request_dict: 发送的数据
        :param import_mod: 导入模块
        :param request_method_name: 请求方法名(request)；requests.request;
        :return: 
        """
        encoding = request_dict.pop("encoding", "")

        validate = request_dict.pop("validate", "")

        extractors = request_dict.pop("extractors", {})

        url = request_dict["url"] = build_url(
            testcase_obj.config.base_url, request_dict["url"]
        )
        # 在配置文件中读取是否需要配置证书
        verify = testcase_obj.config.verify
        # 发送请求的地方，verify=False表示不验证证书
        # getattr(import_mod, request_method_name)(**request_dict)等价于 import_mod.request_method_name(**request_dict)
        res = getattr(import_mod, request_method_name)(verify=verify, **request_dict)
        resp_obj = ResponseObject(res)
        method = request_dict.pop("method")

        # extract
        # 提取内容，并存入变量中
        extract_mapping = resp_obj.extract(extractors)
        self.local_variable.update(extract_mapping)

        # validate

        try:
            resp_obj.validate(validate)
            session_success = True
            # log_req_resp_details()
        except ValidationFailure:
            session_success = False

            self.log_req_resp_details(url, method, request_dict, res)
            raise

    def parse_value(self, content, testcase_obj: TestCase = None):
        """
        解析函数为可执行的函数
        :param content:
        :param testcase_obj: 测试对象
        :return:
        """
        raw = yaml.dump(content)
        # 替换其他的变量为真实的测试数据
        if testcase_obj:
            raw = Template(raw).safe_substitute(testcase_obj.config.variables)
        # r是（rawsting） 的缩写，作用避免少写了\
        functions = re.findall(r"\$\((.*)\)", raw)
        for function in functions:

            if function in self.local_variable.keys():

                raw = raw.replace(f"$({function})", repr(self.local_variable[function]))
            else:
                logger.error(f"{function}not in {self.local_variable.keys()}")

        return yaml.safe_load(raw)

    def run_fun(self, request_key, testcase_obj: TestCase):
        """
        运行方法
        :param request_key: 函数名;eg:test_gettoken
        :param testcase_obj: 测试对象
        eg:
        TestCase包含2个属性(config,teststeps)

        :return:
        """

        try:
            return self.local_variable[request_key].run(testcase_obj)
        except KeyError:
            logger.exception(f"{request_key} not found")
            # raise e

import base64
import importlib
import json
import re

import types
from string import Template
from typing import Union

import yaml
from jsonpath import jsonpath
from loguru import logger

from requests_wework.core.content import Content, PyContent


class BaseAction:
    # 依赖
    depends = []
    # 局部函数表，key是函数名，value 是包含这个函数的类名地址
    local_variable = {}

    """
    
    """

    # 变量名说明
    # yaml_data(yaml中的数据)--》yaml 中的最外层key,value：request_key(dict_key),request_value（dict_value）,
    # -->yaml 第2层中的字典key request_entry_key(dict_key); request_entry_value((dict_value))

    def __init__(self, content: Union[Content, PyContent]):
        """
        1、得到需要的数据
        :param content: 获取数据的类
        """

        self.yaml_data: dict = content.get_data()

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
            # 函数的命名规则都要一个前缀来表面是函数，def_
            elif request_key.startswith("def_"):
                # 去掉函数前缀def_,获取真实的函数名
                request_key = request_key[4:]

                #   tmp_class  类的初始化 方法
                def __init__(s, request_value, request_key):
                    s.request_key = request_key
                    s.request_value = request_value

                # tmp_class 的方法
                def run(s, testData=None):
                    """
                    
                    :param s: 
                    :param testData: 需要参数化的数据
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
                            try:

                                return self.local_variable[request_method_name].run()
                            # 报关键字异常，说明要发送请求了
                            except KeyError:

                                for import_mod in self.depends:
                                    # 判断导入的模块中是否包含属性或方法
                                    if hasattr(import_mod, request_method_name):
                                        content_format = self.parse_value(
                                            request_entry_value, testData
                                        )
                                        # 把int 类型的mobile 转换为str类型
                                        if content_format.__contains__("json"):
                                            if content_format["json"].__contains__(
                                                "mobile"
                                            ):
                                                content_format["json"]["mobile"] = str(
                                                    content_format["json"]["mobile"]
                                                )

                                        # 这句代码实际就是调用是发送请求的地方
                                        return self.send(
                                            content_format,
                                            import_mod,
                                            request_method_name,
                                        )

                cls_dict = {"__init__": __init__, "run": run}
                # 动态创建class, 在回调函数中传入方法run和init,并没有调用类
                tmp_class = types.new_class(
                    "tmp_class", (), {}, lambda ns: ns.update(cls_dict)
                )
                # 把方法名作为key,类地址作为value存入字典--》eg:<class 'dict'>: {'get_token': <types.tmp_class object at 0x0552E388>}
                # 实例化类
                self.local_variable[request_key] = tmp_class(request_value, request_key)

    def send(self, content_format: dict, import_mod, request_method_name):
        """
        发送请求入口
        :param content_format: 发送的数据
        :param import_mod: 导入模块
        :param request_method_name: 请求方法名(request)；requests.request;
        :return: 
        """
        # todo
        env = yaml.safe_load(
            open(r"C:\Users\lnz\PycharmProjects\HGS\requests_wework\api\env.yaml")
        )
        req_dict = content_format.copy()
        if content_format.__contains__("encoding"):
            req_dict.pop("encoding")
        if content_format.__contains__("validate"):
            req_dict.pop("validate")
        req_dict["url"] = str(env["env"][env["default"]]) + str(req_dict["url"])
        # 发送请求的地方，verify=False表示不验证证书
        # getattr(import_mod, request_method_name)(**content_format)等价于 import_mod.request_method_name(**content_format)
        res = getattr(import_mod, request_method_name)(verify=False, **req_dict)
        # 对返回结果进行处理
        # 如果字典的key包含encoding
        if content_format.__contains__("encoding"):
            if content_format["encoding"] == "base64":
                response_json = json.loads(base64.b64decode(res.content))
                return self.validate(content_format, response_json)
            elif content_format["encoding"] == "private":
                # todo
                return getattr(import_mod, request_method_name)("url", data=res.content)
            else:
                # todo
                pass
        else:
            # 调用断言方法
            return self.validate(content_format, res)

    def validate(self, request_json: dict, response):
        """
        
        :param request_json: 请求的数据
        :param response: 响应的数据
        :return: 
        """
        validate_list = request_json.get("validate", [])
        for item in validate_list:
            # eq这种方式已完善
            if item.get("eq", []):
                validate_key: str = item["eq"][0]
                if validate_key.find("body") != -1:
                    validate_key = validate_key.replace("body.", "")
                    act_value = jsonpath(response.json(), f"$.{validate_key}")[0]
                elif validate_key.find("status_code") != -1:
                    act_value = getattr(response, validate_key)
                elif validate_key.find("headers") != -1:
                    validate_key = validate_key.replace("headers.", "")
                    act_value = response.headers.get(validate_key)
                else:
                    # todo
                    act_value = []
                    pass
                except_value = item["eq"][1]
                assert except_value == act_value
            else:
                # todo
                pass

        return response.json()

    def parse_value(self, content, testData=None):
        """
        解析函数为可执行的函数？？
        :param content:
        :param testData: 测试数据
        :return:
        """
        raw = yaml.dump(content)
        # 替换其他的变量为真实的测试数据
        if testData:
            raw = Template(raw).safe_substitute(testData)
        # r是（rawsting） 的缩写，作用避免少写了\
        functions = re.findall(r"\$\((.*)\)", raw)
        for function in functions:
            # 解析到有函数就要调用run_run方法
            parse_res = self.run_fun(function, testData)
            # 以下判断的代码暂时未使用
            # todo
            if "access_token" in parse_res.keys():
                raw = raw.replace(f"$({function})", repr(parse_res["access_token"]))
            else:
                raw = raw.replace(f"$({function})", repr(parse_res))
        return yaml.safe_load(raw)

    def run_fun(self, request_key, testData: dict = None):
        """
        运行方法
        :param request_key: 函数名
        :param testData: 测试数据(需要参数的测试数据)
        :return:
        """

        try:
            return self.local_variable[request_key].run(testData)
        except KeyError as e:
            raise e

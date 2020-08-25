import base64
import importlib
import json
import re
import types
from string import Template

import yaml
from jsonpath import jsonpath

from requests_wework.core.content import Content


class BaseAction:
    # 依赖
    depends = []
    # 局部函数表，key是函数名，value 是包含这个函数的类名地址
    local_variable = {}

    def __init__(self, content: Content):
        self.data = content.get_data()
        # 扫描函数，把函数存入局部变量表
        self.parse_content()

    # 解析yaml中的内容
    def parse_content(self):
        for command_name, command_content in self.data.items():
            if "depend" == command_name:
                # 循环导入
                for depend in command_content:
                    self.depends.append(importlib.import_module(depend))
            # 函数的命名规则都要一个前缀来表面是函数，def_
            elif command_name.startswith('def_'):
                # 去掉函数前缀def_,获取真实的函数名
                fun_name = command_name[4:]

                #   tmp_class  类的初始化 方法
                def __init__(s, int_command_content, in_fun_name):
                    s.fun_name = in_fun_name
                    s.command_content = int_command_content

                # tmp_class 的方法
                def run(s, testData=None):
                    for in_command_name, in_command_content in s.command_content.items():
                        # 判断方法名的前置是run_
                        if in_command_name.startswith('run_'):
                            # 切割列表得到真实的方法名
                            in_fun_name = in_command_name[4:]
                            try:
                                return self.local_variable[in_fun_name].run()
                            except KeyError:

                                for import_mod in self.depends:
                                    # 判断导入的模块中是否包含属性或方法in_fun_name
                                    if hasattr(import_mod, in_fun_name):
                                        content_format = self.parse_value(in_command_content, testData)
                                        # 把int 类型的mobile 转换为str类型
                                        if content_format.__contains__('json'):
                                            if content_format['json'].__contains__('mobile'):
                                                content_format['json']['mobile'] = str(content_format['json']['mobile'])
                                        # getattr(import_mod, in_fun_name)(**content_format)等价于 import_mod.in_fun_name(**content_format)
                                        # 这句代码实际就是requests.request(**content_format).json() ,是发送请求的地方
                                        return self.send(content_format, import_mod, in_fun_name)

                cls_dict = {
                    '__init__': __init__,
                    'run': run
                }
                # 动态创建class, 在回调函数中传入方法run和init
                tmp_class = types.new_class('tmp_class', (), {}, lambda ns: ns.update(cls_dict))
                # 把方法名作为key,类地址作为value存入字典--》eg:<class 'dict'>: {'get_token': <types.tmp_class object at 0x0552E388>}
                self.local_variable[fun_name] = tmp_class(command_content, fun_name)

    def send(self, content_format: dict, import_mod, in_fun_name):
        # todo
        env = yaml.safe_load(
            open(r'C:\Users\lnz\PycharmProjects\HGS\requests_wework\api\env.yaml'))
        req_dict = content_format.copy()
        if content_format.__contains__('encoding'):
            req_dict.pop('encoding')
        if content_format.__contains__('validate'):
            req_dict.pop('validate')
        req_dict['url'] = str(env['env'][env['default']]) + str(
            req_dict['url'])
        # 发送请求的地方，verify=False表示不验证证书
        res = getattr(import_mod, in_fun_name)(verify=False, **req_dict)
        # 对返回结果进行处理
        # 如果字典的key包含encoding
        if content_format.__contains__('encoding'):
            if content_format['encoding'] == 'base64':
                response_json = json.loads(base64.b64decode(res.content))
                return self.validate(content_format, response_json)
            elif content_format['encoding'] == 'private':
                # todo
                return getattr(import_mod, in_fun_name)('url', data=res.content)
            else:
                # todo
                pass
        else:

            return self.validate(content_format, res)

    def validate(self, request_json: dict, response):
        '''
        验证断言
        :return:
        '''
        validate_list = request_json.get('validate', [])
        for item in validate_list:
            # eq这种方式已完善
            if item.get('eq', []):
                validate_key: str = item['eq'][0]
                if validate_key.find('body') != -1:
                    validate_key = validate_key.replace('body.', '')
                    act_value = jsonpath(response.json(), f'$.{validate_key}')[0]
                elif validate_key.find('status_code') != -1:
                    act_value = getattr(response, validate_key)
                elif validate_key.find('headers') != -1:
                    validate_key = validate_key.replace('headers.', '')
                    act_value = response.headers.get(validate_key)
                else:
                    # todo
                    act_value = []
                    pass
                except_value = item['eq'][1]
                assert except_value == act_value
            else:
                # todo
                pass

        return response.json()

    def parse_value(self, content, testData=None):
        '''
        解析函数为可执行的函数？？
        :param content:
        :param testData: 测试数据
        :return:
        '''
        raw = yaml.dump(content)
        # 替换其他的变量为真实的测试数据
        if testData:
            raw = Template(raw).safe_substitute(testData)
        # r是（rawsting） 的缩写，作用避免少写了\
        functions = re.findall(r"\$\((.*)\)", raw)
        for function in functions:
            # 解析到有函数就要调用run_run方法
            parse_res = self.run_fun(function, testData)
            if "access_token" in parse_res.keys():
                raw = raw.replace(f"$({function})", repr(parse_res["access_token"]))
            else:
                raw = raw.replace(f"$({function})", repr(parse_res))
        return yaml.safe_load(raw)

    def run_fun(self, fun_name, testData: dict = None):
        '''
        运行方法
        :param fun_name: 函数名
        :param testData: 测试数据
        :return:
        '''
        return self.local_variable[fun_name].run(testData)

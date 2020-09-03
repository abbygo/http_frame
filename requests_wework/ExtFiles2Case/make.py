import subprocess
import sys
from pathlib import Path
from typing import Dict, Text, NoReturn

import jinja2
import yaml
from loguru import logger
from sentry_sdk import capture_exception

from requests_wework.ExtFiles2Case.utils import is_support_multiprocessing


def format_pytest_with_black(*python_paths: Text) -> NoReturn:
    logger.info("format pytest cases with black ...")
    try:
        if is_support_multiprocessing() or len(python_paths) <= 1:
            subprocess.run(["black", *python_paths])
        else:
            logger.warning(
                f"this system does not support multiprocessing well, format files one by one ..."
            )
            [subprocess.run(["black", path]) for path in python_paths]
    except subprocess.CalledProcessError as ex:
        capture_exception(ex)
        logger.error(ex)
        sys.exit(1)
    except FileNotFoundError:
        err_msg = """
missing dependency tool: black
install black manually and try again:
$ pip install black
"""
        logger.error(err_msg)
        sys.exit(1)
def prepare_content(yamlcontent: Dict):
    '''
    准备内容
    :param yamlcontent:
    :return:
    eg:
    test_gettoken:
        method: GET
        url: https://qyapi.weixin.qq.com/cgi-bin/gettoken
        params:
            corpid: xx
        headers:
            Host: qyapi.weixin.qq.com
        validate:
        -   eq:
            - status_code
            - 200
    '''
    if yamlcontent.get('depend'):
        yamlcontent.pop('depend')
        request_entry_dict = {}
        for requst_key, request_entry in yamlcontent.items():
            request_entry_dict[requst_key] = request_entry['run_request']
        return request_entry_dict
    else:
        return yamlcontent



def make_config_chain_style(config: Dict) -> Text:
    '''

    :param config:
    :return:
    '''
    config_chain_style = f'Config("{config["name"]}")'

    if config["variables"]:
        variables = config["variables"]
        config_chain_style += f".variables(**{variables})"

    if "base_url" in config:
        config_chain_style += f'.base_url("{config["base_url"]}")'

    if "verify" in config:
        config_chain_style += f'.verify({config["verify"]})'

    if "export" in config:
        config_chain_style += f'.export(*{config["export"]})'

    if "weight" in config:
        config_chain_style += f'.locust_weight({config["weight"]})'

    return config_chain_style


def make_request_chain_style(request: Dict) -> Text:
    '''
    构造请求字符串
    :param request:
    eg:
   {
    "method": "GET",
    "url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
    "params": {
        "corpid": "x3",

    },
    "headers": {
        "Host": "qyapi.weixin.qq.com",
    },
    "validate": [
        {
            "eq": [
                "status_code",
                200
            ]
        },]}
    :return:
    eg:
     .get("https://qyapi.weixin.qq.com/cgi-bin/gettoken")
    .with_params(
        **{
            "corpid": "wwf2dbb0a93f2eac33",
        }
    )
    .with_headers(
        **{
            "Host": "qyapi.weixin.qq.com",
        }
    )
    .validate()
    .assert_equal("status_code", 200)

    '''
    method = request["method"].lower()
    url = request["url"]
    request_chain_style = f'.{method}("{url}")'

    if "params" in request:
        params = request["params"]
        request_chain_style += f".with_params(**{params})"

    if "headers" in request:
        headers = request["headers"]
        request_chain_style += f".with_headers(**{headers})"

    if "cookies" in request:
        cookies = request["cookies"]
        request_chain_style += f".with_cookies(**{cookies})"

    if "data" in request:
        data = request["data"]
        if isinstance(data, Text):
            data = f'"{data}"'
        request_chain_style += f".with_data({data})"

    if "json" in request:
        req_json = request["json"]
        if isinstance(req_json, Text):
            req_json = f'"{req_json}"'
        request_chain_style += f".with_json({req_json})"

    if "timeout" in request:
        timeout = request["timeout"]
        request_chain_style += f".set_timeout({timeout})"

    if "verify" in request:
        verify = request["verify"]
        request_chain_style += f".set_verify({verify})"

    if "allow_redirects" in request:
        allow_redirects = request["allow_redirects"]
        request_chain_style += f".set_allow_redirects({allow_redirects})"

    if "upload" in request:
        upload = request["upload"]
        request_chain_style += f".upload(**{upload})"
    if "validate" in request:
        validate_list = request["validate"]
        if validate_list:
            request_chain_style += f".validate()"
            for item in validate_list:
                for key, value in item.items():
                    if key in ['eq', 'equal']:


                        if '"' in value[0]:
                            # e.g. body."user-agent" => 'body."user-agent"'
                            value[0] = f"'{value[0]}'"
                        else:
                            value[0] = f'"{value[0]}"'
                        if isinstance(value[1], Text):
                            value[1] = f'"{value[1]}"'
                            # todo
                        # .assert_equal("headers.Content-Type"', "application/json; charset=UTF-8") 这个情况断言也有问题
                        request_chain_style += f".assert_equal({value[0]}, {value[1]})"

    return request_chain_style


def pare_case_content(data, file_name, class_name, open_file_name):
    '''
    解析yaml中的内容,为py文件的内容做准备
    类名，方法名，调用的文件名
    :param data:
    :param file_name:
    :return:
    '''

    fun_list = []
    for command_name, command_content in data.items():
        # 函数的命名规则都要一个前缀来表示函数，test_
        if command_name.startswith('test_'):
            fun_list.append(command_name)
    # 构造类名
    class_name = f"Test_{class_name}"
    return gen_py_testcase(fun_list, file_name, class_name, open_file_name)


def gen_py_testcase_no_yaml(content: dict, file_name, class_name):
    '''
    生成测试用例文件,不需要先有yaml或json文件作为基础

    '''
    # 类名，方法名，文件名，方法，url,参数，头信息，断言，
    logger.info("testcase to py format.")
    __TEMPLATE__ = jinja2.Template(
        """# NOTE: Generated By Runner v0.0.2

from requests_wework.core.runner import PareStep
from requests_wework.core.testcase import Step, RunRequest, Config


class {{ class_name }}(PareStep):
    config = (
        Config("request methods testcase: reference testcase")
        .verify(False)
    )
    
{% for key,value in request_entry_dict.items() %}
    def {{key}}(self):
        self.start(
            Step(
                RunRequest(){{make_request_chain_style(value)}}
                )
            )

    {% endfor %}
    
"""
    )
    request_entry_dict = prepare_content(content)
    data = {
        "class_name": class_name,
        "make_request_chain_style": make_request_chain_style,
        "request_entry_dict": request_entry_dict
    }
    # 渲染模板
    content = __TEMPLATE__.render(data)
    # 新产生py文件
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    format_pytest_with_black(file_name)
    logger.info("Generate py testcase successfully: {}".format(file_name))


def gen_py_testcase(fun_list, file_name, class_name, open_file_name):
    '''
    生成测试用例文件,需要先有yaml或json文件作为基础
    :param fun_list: 方法名
    :param file_name: 需要新产生的文件名
    :param class_name: 需要新产生的类名
    :return:
    '''
    logger.info("testcase to py format.")
    __TEMPLATE__ = jinja2.Template(
        """# NOTE: Generated By Runner v0.0.1

from requests_wework.testcases.base_case import BaseCase
class {{ class_name }}(BaseCase):
    {% for item in  fun_list %}
         def {{item}}(self):
            r = self.basecase(r"{{open_file_name}}")
    {% endfor %}

"""
    )
    data = {
        "fun_list": fun_list,
        "file_name": file_name,
        "class_name": class_name,
        "open_file_name": open_file_name
    }
    # 渲染模板
    content = __TEMPLATE__.render(data)
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    format_pytest_with_black(file_name)
    logger.info("Generate py testcase successfully: {}".format(file_name))


def call_gen_py_testcase(open_file_name):
    '''
    调用生成测试用例方法
    :param file_name:需要生成的文件名
    :return:
    '''
    p = Path(open_file_name)
    with open(open_file_name, encoding='utf-8') as f:
        res = yaml.safe_load(f)
        parent_path = p.joinpath(p.parent, f"test_{p.stem}.py")
        return pare_case_content(res, parent_path, p.stem, open_file_name)

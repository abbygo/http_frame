import base64
import json
import os
import sys
import urllib.parse as urlparse
from json import JSONDecodeError
from typing import Text

from pathlib import Path
from sentry_sdk import capture_exception
from loguru import logger
import yaml

from requests_wework.har2ncase.utils import convert_x_www_form_urlencoded_to_dict, convert_list_to_dict
def ensure_file_path(path: Text) -> Text:
    if not path:
        logger.error("HAR file not specified.")
        sys.exit(1)
    if not path.endswith(".har"):
        if not os.path.isdir(path):
            logger.error("HAR file not specified.")
            sys.exit(1)
    # path = ensure_path_sep(path)
    if not os.path.isfile(path):
        logger.error(f"HAR file not exists: {path}")
        sys.exit(1)

    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)

    return path

class HarParser(object):
    def __init__(self, har_file_path, filter_str=None, exclude_str=None):
        self.har_file_path = ensure_file_path(har_file_path)
        self.filter_str = filter_str
        self.exclude_str = exclude_str or ""

    def make_request_method(self, teststep_dict, request_json):
        '''
        提取请求方法
        '''
        method = request_json.get("method")
        if not method:
            logger.exception("method missed in request.")
            sys.exit(1)

        teststep_dict["method"] = method

    def pre_header(self, teststep_dict, request_json):
        '''
        构造请求头
        :param request_json: 请求json
        :param testcase:测试用例
        :return:
        '''
        teststep_headers = {}
        for header in request_json.get("headers", []):
            teststep_headers[header["name"]] = header["value"]

            if teststep_headers:
                teststep_dict["headers"] = teststep_headers

    def __make_request_cookies(self, teststep_dict, request_json):
        '''
        提取cookie
        :param teststep_dict:
        :param request_json:
        :return:
        '''
        cookies = {}
        for cookie in request_json.get("cookies", []):
            cookies[cookie["name"]] = cookie["value"]

        if cookies:
            teststep_dict["cookies"] = cookies

    def __make_request_url(self, teststep_dict, request_json):
        '''
        提取url和请求参数
        :param teststep_dict:
        :param request_json:
        :return:
        '''
        url = request_json.get("url")

        request_params = convert_list_to_dict(
            request_json.get("queryString", [])
        )
        parsed_object = urlparse.urlparse(url)
        '''
        抓包工具导出的url中有参数，为了获取url.需要去掉参数
        '''
        if request_params:
            '''
            下一句是把参数替换为空白
            '''
            parsed_object = parsed_object._replace(query="")
            teststep_dict["url"] = parsed_object.geturl()
            teststep_dict["params"] = request_params
        else:
            teststep_dict["url"] = url

    def _make_request_data(self, teststep_dict, request_json):
        """ parse HAR entry request data, and make teststep request data
            提取请求体中的数据

            """
        method = request_json.get("method")
        if method in ["POST", "PUT", "PATCH"]:
            postData = request_json.get("postData", {})
            mimeType = postData.get("mimeType")

            # Note that text and params fields are mutually exclusive.
            if "text" in postData:
                post_data = postData.get("text")
            else:
                params = postData.get("params", [])
                post_data = convert_list_to_dict(params)

            request_data_key = "data"
            if not mimeType:
                pass
            elif mimeType.startswith("application/json"):
                try:
                    post_data = json.loads(post_data)
                    request_data_key = "json"
                except JSONDecodeError:
                    pass
            elif mimeType.startswith("application/x-www-form-urlencoded"):
                post_data = convert_x_www_form_urlencoded_to_dict(post_data)
            else:
                # TODO: make compatible with more mimeType
                pass

            teststep_dict[request_data_key] = post_data

    def _make_validate(self, teststep_dict, response_json):
        """ parse HAR entry response and make teststep validate.
        生成断言
        Args:
            entry_json (dict):
                {
                    "request": {},
                    "response": {
                        "status": 200,
                        "headers": [
                            {
                                "name": "Content-Type",
                                "value": "application/json; charset=utf-8"
                            },
                        ],
                        "content": {
                            "size": 71,
                            "mimeType": "application/json; charset=utf-8",
                            "text": "eyJJc1N1Y2Nlc3MiOnRydWUsIkNvZGUiOjIwMCwiTWVzc2FnZSI6bnVsbCwiVmFsdWUiOnsiQmxuUmVzdWx0Ijp0cnVlfX0=",
                            "encoding": "base64"
                        }
                    }
                }

        Returns:
            {
                "validate": [
                    {"eq": ["status_code", 200]}
                ]
            }

        """
        teststep_dict["validate"].append(
            {"eq": ["status_code", response_json.get("status")]}
        )

        resp_content_dict = response_json.get("content")

        headers_mapping = convert_list_to_dict(
            response_json.get("headers", [])
        )
        if "Content-Type" in headers_mapping:
            teststep_dict["validate"].append(
                {"eq": ["headers.Content-Type", headers_mapping["Content-Type"]]}
            )

        text = resp_content_dict.get("text")
        if not text:
            return

        mime_type = resp_content_dict.get("mimeType")
        if mime_type and mime_type.startswith("application/json"):

            encoding = resp_content_dict.get("encoding")
            if encoding and encoding == "base64":
                content = base64.b64decode(text)
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    logger.warning(f"failed to decode base64 content with utf-8 !")
                    return
            else:
                content = text

            try:
                resp_content_json = json.loads(content)
            except JSONDecodeError:
                logger.warning(f"response content can not be loaded as json: {content}")
                return

            if not isinstance(resp_content_json, dict):
                # e.g. ['a', 'b']
                return

            for key, value in resp_content_json.items():
                if isinstance(value, (dict, list)):
                    continue

                teststep_dict["validate"].append({"eq": ["body.{}".format(key), value]})

    def _prepare_teststeps(self, harfile):
        """ make teststep list.
            准备yaml文件格式的数据
        eg:*.yaml

    depend:
    - requests
    def_gettoken:
        run_request:
            validate:
            -   eq:
                - status_code
                - 200
            method: GET
            url: /cgi-bin/gettoken
            params:
                corpid: wwf2dbb0a93f2eac33
                corpsecret: fmDbF_Ll4GPiYmrqHrqtztTTVkbG6Z1NqXjiJ-eQ1gc
            headers:
                Connection: keep-alive

        """
        with open(rf"{harfile}", 'rb') as file:
            yaml_content = json.load(file)
            entry_json = yaml_content['log']['entries']
            # 构造要生成的yaml内容
            content_dict = {"depend": ["requests"]}
            for item in entry_json:
                request_json = item['request']
                response_json = item['response']
                parsed_object = urlparse.urlparse(request_json['url'])
                # 从url中获取方法名
                if parsed_object.path.find('/') != -1:
                    name = parsed_object.path.split('/')[-1]
                else:
                    name = parsed_object.path

                # 方法名
                fun_name = "def_" + name
                # 请求的字典
                request_dict = {}
                # 方法
                self.make_request_method(request_dict, request_json)
                # url和参数

                self.__make_request_url(request_dict, request_json)
                self.__make_request_cookies(request_dict, request_json)
                self.pre_header(request_dict, request_json)
                self._make_request_data(request_dict, request_json)
                # 构造断言列表
                request_dict['validate'] = []
                self._make_validate(request_dict, response_json)
                content_dict[fun_name] = {"run_request": request_dict}

        return content_dict

    def gen_testcase(self, file_type="YAML"):
        '''
        生成yaml\json测试文件
        :param file_type: 文件类型
        :return: yaml或json文件
        '''
        logger.info(f"Start to generate testcase from {self.har_file_path}")
        try:
            content_dict = self._prepare_teststeps(self.har_file_path)
        except Exception as ex:
            capture_exception(ex)
            raise

        p = Path(rf"{self.har_file_path}")
        output_testcase_file = ''
        # 构造要生成的文件绝对路径
        parent_path = p.joinpath(p.parent, p.stem)
        if file_type == "JSON":
            output_testcase_file = f"{parent_path}.json"
            dump_json(content_dict,
                      rf'{output_testcase_file}')
        elif file_type == "YAML":
            output_testcase_file = f"{parent_path}.yaml"
            dump_yaml(content_dict,
                      rf'{output_testcase_file}')
        if output_testcase_file:
            # logger.info(f"generated testcase: {output_testcase_file}")
            return output_testcase_file
        else:
            logger.exception("-2y|-2j prameter missed in request.")
            sys.exit(1)






def dump_json(testcase, json_file):
    """ dump HAR entries to json testcase
    """
    logger.info("dump testcase to JSON format.")

    with open(json_file, "w", encoding="utf-8") as outfile:
        my_json_str = json.dumps(testcase, ensure_ascii=False, indent=4)
        if isinstance(my_json_str, bytes):
            my_json_str = my_json_str.decode("utf-8")

        outfile.write(my_json_str)

    logger.info("Generate JSON testcase successfully: {}".format(json_file))


def dump_yaml(testcase, yaml_file):
    """ dump HAR entries to yaml testcase
    """
    logger.info("dump testcase to YAML format.")

    with open(yaml_file, "w", encoding="utf-8") as outfile:
        yaml.safe_dump(testcase, outfile, allow_unicode=True, default_flow_style=False, indent=4, sort_keys=False)









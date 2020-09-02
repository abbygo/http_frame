import base64
import json
import os
import sys
import urllib.parse as urlparse
from json import JSONDecodeError
from typing import Text, Dict, List

from pathlib import Path
from sentry_sdk import capture_exception
from loguru import logger
import yaml

from requests_wework.core.parser import get_status_code
from requests_wework.ExtFiles2Case.make import (
    gen_py_testcase_no_yaml,
    call_gen_py_testcase,
)
from requests_wework.ExtFiles2Case.utils import (
    convert_x_www_form_urlencoded_to_dict,
    convert_list_to_dict,
)


def ensure_file_path(path: Text, file_extension: Text = "har") -> Text:
    """

    :param path:
    :param file_extension: 文件后缀
    :return:
    """
    if not path:
        logger.error(f"{file_extension} file not specified.")
        sys.exit(1)
    if not path.endswith(f".{file_extension}"):
        if not os.path.isdir(path):
            logger.error(f"{file_extension} file not specified.")
            sys.exit(1)
    # path = ensure_path_sep(path)
    if not os.path.isfile(path):
        logger.error(f"{file_extension} file not exists: {path}")
        sys.exit(1)

    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)

    return path


class PostManParser(object):
    def __init__(self, postman_file_path):
        self.postman_file_path = ensure_file_path(postman_file_path, "json")
        self.output_path_contain_stem, self.output_dir = make_output_dir(self.postman_file_path)

    """
    分析：postman 的数据内容是放到item下的列表中，列表包含了字典，一个字典包含完整请求，一共
    4个部分：name,event,request,response

    eg:
    {
	"info": {
	},
	"item": [
		{
			"name": "get请求",
			"event": [
			],
			"request": {

			},
			"response": []
		},
	}
    """

    def read_content(self):
        """
        读取postman文件内容
        :return:
        """
        if os.path.isfile(self.postman_file_path):
            try:
                with open(self.postman_file_path, encoding="utf-8") as file:

                    postman_content = json.load(file)
                    return postman_content
            except:
                # todo
                # 具体异常
                raise

        else:
            logger.error(f"{self.postman_file_path} is not a file")
            sys.exit(1)

    def prepare_entry(self, postman_content: Dict):
        """
        准备数据
        :return:
        {'test_get': {'method': 'GET',-----}}
        """
        total_data = {}
        item: List = postman_content.pop("item")
        for entry in item:
            requst_entry = {}
            request: Dict = entry.get("request")
            event: List = entry.get("event")
            method = {"method": request["method"]}
            url, params = self.make_url(request["url"])
            # path会有多个，取最后一个
            path = request["url"]["path"][-1]
            # 有些path的路径是-，需要替换为_
            path = path.replace("-", "_")
            # 方法名
            fun_name = f"test_{path}"
            requst_entry.update(method)
            requst_entry.update(url)
            if params:
                requst_entry.update(params)

            if request.get("header"):
                headers = {"headers": convert_list_to_dict(request.get("header"))}
                if headers:
                    requst_entry.update(headers)
            if request.get("auth"):
                auth_headers = self.make_auth_header(request.get("auth"))
                if auth_headers:
                    # 有认证信息头
                    if requst_entry.get("headers"):
                        requst_entry.get("headers").update(auth_headers)
                    else:
                        requst_entry["headers"] = auth_headers
            if request.get("body"):
                body = self.make_body(method, request.get("body"))
                if body:
                    requst_entry.update(body)

            if event:
                validate = self.make_validate(event)
                if validate:
                    requst_entry.update(validate)
            total_data[fun_name] = requst_entry
        return total_data

    def make_auth_header(self, auth: Dict):
        """
        获取认证信息中头信息
        :param auth:
        :return:
        """
        if auth.get("type") == "basic":
            auth_list = convert_list_to_dict(auth.get("basic"))
            return auth_list
        else:
            pass

    #         todo

    def make_validate(self, event: List):
        """
        构造validate
        :param event: eg:
        [
				{
					"listen": "test",
					"script": {
						"id": "fda4a0f5-1526-4526-8313-7cbc95a0e4d1",
						"exec": [
							"pm.test(\"Status code is 200\", function () {\r",
							"    pm.response.to.have.status(200);\r",
							"});"
						],
						"type": "text/javascript"
					}
				}
			],
        :return:
        "validate": [
                {
                    "eq": [
                        "status_code",
                        200
                    ]
                }
        ]
        """
        validate_list = []
        for i in event:
            if i.get("script"):
                if i.get("script").get("exec"):
                    exec_list: List = i.get("script").get("exec")
                    try:
                        # todo
                        # 获取其他类型断言，目前只提取了状态码的这种

                        value = exec_list[1]
                        # 正则提取状态码
                        status_code = get_status_code(value)
                        # 添加到列表中
                        if status_code:
                            item = {"eq": ["status_code", int(status_code)]}
                            validate_list.append(item)

                    except ValueError:
                        pass
        if validate_list:
            return {"validate": validate_list}

    def make_url(self, raw_url: Dict):
        """
        提取url
        :param raw_url:
        :return:
        """
        params = ""
        raw: Text = raw_url["raw"]
        if raw.find("?") != -1:
            raw_list = raw_url["raw"].split("?")
            url = raw_list[0]
            params = convert_list_to_dict(raw_url["query"])
        else:
            url = raw_url["raw"]

        if params:

            return {"url": url}, {"params": params}
        else:
            return {"url": url}, params

    def make_body(self, method, body: Dict):
        requst_data = {}
        if method not in ["GET", "get"]:
            if body.get("mode"):
                if body.get("mode") == "formdata":
                    value = convert_list_to_dict(body.get("formdata"))
                    requst_data["data"] = value
                    return requst_data
                if body.get("mode") == "raw":
                    if body.get("options"):
                        if body.get("options")["raw"]["language"] == "json":

                            value = body.get("raw")

                            requst_data["json"] = eval(value)
                            return requst_data
                        elif body.get("options")["raw"]["language"] == "javascript":
                            pass
                        #         todo
                        elif body.get("options")["raw"]["language"] == "xml":
                            pass
                    #         todo

                    else:
                        # todo
                        # 是否需要添加'Content-Type': 'text/plain'

                        requst_data["data"] = body.get("raw")
                        return requst_data
                if body.get("mode") == "binary":
                    pass

    #                     todo
    #                     x-www-form-urlencode

    def call_gen_python_testcase_by_postman(self):
        """
        调用方法，直接生成可运行的python文件(不需要准备yaml文件)


        """
        logger.info(f"Start to generate testcase from {self.postman_file_path}")
        try:
            content = self.read_content()

            content_dict = self.prepare_entry(content)

            p = Path(self.postman_file_path)
            class_name = f"Test{p.stem}"
            file_name = f"test_{p.stem}.py"
            full_path_name=Path.joinpath(self.output_dir,file_name)
            gen_py_testcase_no_yaml(content_dict, full_path_name, class_name)

        except Exception as ex:
            capture_exception(ex)
            raise


class HarParser(object):
    def __init__(self, har_file_path, filter_str=None, exclude_str=None):
        self.har_file_path = ensure_file_path(har_file_path)
        self.filter_str = filter_str
        self.exclude_str = exclude_str or ""
        self.output_path_contain_stem, self.output_dir = make_output_dir(self.har_file_path)


    def make_request_method(self, teststep_dict, request_json):
        """
        提取请求方法
        """
        method = request_json.get("method")
        if not method:
            logger.exception("method missed in request.")
            sys.exit(1)

        teststep_dict["method"] = method

    def prepare_header(self, teststep_dict, request_json):
        """
        构造请求头
        :param request_json: 请求json
        :param testcase:测试用例
        :return:
        """
        teststep_headers = {}
        for header in request_json.get("headers", []):
            teststep_headers[header["name"]] = header["value"]

            if teststep_headers:
                teststep_dict["headers"] = teststep_headers

    def __make_request_cookies(self, teststep_dict, request_json):
        """
        提取cookie
        :param teststep_dict:
        :param request_json:
        :return:
        """
        cookies = {}
        for cookie in request_json.get("cookies", []):
            cookies[cookie["name"]] = cookie["value"]

        if cookies:
            teststep_dict["cookies"] = cookies

    def __make_request_url(self, teststep_dict, request_json):
        """
        提取url和请求参数
        :param teststep_dict:
        :param request_json:
        :return:
        """
        url = request_json.get("url")

        request_params = convert_list_to_dict(request_json.get("queryString", []))
        parsed_object = urlparse.urlparse(url)
        """
        抓包工具导出的url中有参数，为了获取url.需要去掉参数
        """
        if request_params:
            """
            下一句是把参数替换为空白
            """
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

        headers_mapping = convert_list_to_dict(response_json.get("headers", []))
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

    def _prepare_data_by_har(self, harfile):
        """ make teststep list.
            由har后缀的数据转换为特定格式的数据
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
        with open(rf"{harfile}", "rb") as file:
            yaml_content = json.load(file)
            entry_json = yaml_content["log"]["entries"]
            # 构造要生成的yaml内容
            content_dict = {"depend": ["requests"]}
            for item in entry_json:
                request_json = item["request"]
                response_json = item["response"]
                parsed_object = urlparse.urlparse(request_json["url"])
                # 从url中获取方法名
                if parsed_object.path.find("/") != -1:
                    name = parsed_object.path.split("/")[-1]
                else:
                    name = parsed_object.path

                # 方法名
                fun_name = "test_" + name
                # 请求的字典
                request_dict = {}
                # 方法
                self.make_request_method(request_dict, request_json)
                # url和参数

                self.__make_request_url(request_dict, request_json)
                self.__make_request_cookies(request_dict, request_json)
                self.prepare_header(request_dict, request_json)
                self._make_request_data(request_dict, request_json)
                # 构造断言列表
                request_dict["validate"] = []
                self._make_validate(request_dict, response_json)
                content_dict[fun_name] = {"run_request": request_dict}

        return content_dict

    def gen_testcase(self, file_type="pytest"):
        """
        生成yaml\json\py测试文件
        :param file_type: 文件类型
        :return: yaml或json文件
        """
        logger.info(f"Start to generate testcase from {self.har_file_path}")
        try:
            content_dict = self._prepare_data_by_har(self.har_file_path)
        except Exception as ex:
            capture_exception(ex)
            raise



        if file_type == "JSON":
            output_testcase_file = f"{self.output_path_contain_stem}.json"
            dump_json(content_dict, rf"{output_testcase_file}")
            logger.info(f"generated testcase: {output_testcase_file}")
            call_gen_py_testcase(output_testcase_file)
        elif file_type == "YAML":
            output_testcase_file = f"{self.output_path_contain_stem}.yaml"
            dump_yaml(content_dict, rf"{output_testcase_file}")
            logger.info(f"generated testcase: {output_testcase_file}")

            call_gen_py_testcase(output_testcase_file)
        else:
            # 调用生成python文件 的方法

            self.call_gen_python_testcase()

    def call_gen_python_testcase(self):
        """
        调用方法，直接生成可运行的python文件(不需要准备yaml文件)
        :param file_type: 文件类型

        """
        logger.info(f"Start to generate testcase from {self.har_file_path}")
        try:
            content_dict = self._prepare_data_by_har(self.har_file_path)
            p = Path(self.har_file_path)
            class_name = f"Test{p.stem}"
            file_name = f"test_{p.stem}.py"
            full_path_name=Path.joinpath(self.output_dir,file_name)
            gen_py_testcase_no_yaml(content_dict, full_path_name, class_name)

        except Exception as ex:
            capture_exception(ex)
            raise


def dump_json(testcase, json_file):
    """ dump HAR entries to json testcase
    """
    logger.info("dump testcase to JSON format.")

    with open(json_file, "w", encoding="utf-8") as outfile:
        my_json_str = json.dumps(testcase, ensure_ascii=False, indent=4)
        if isinstance(my_json_str, bytes):
            my_json_str = my_json_str.decode("utf-8")

        outfile.write(my_json_str)

    # logger.info("Generate JSON testcase successfully: {}".format(json_file))


def dump_yaml(testcase, yaml_file):
    """ dump HAR entries to yaml testcase
    """
    logger.info("dump testcase to YAML format.")

    with open(yaml_file, "w", encoding="utf-8") as outfile:
        yaml.safe_dump(
            testcase,
            outfile,
            allow_unicode=True,
            default_flow_style=False,
            indent=4,
            sort_keys=False,
        )
def make_output_dir(file_path:Text):
    p = Path(rf"{file_path}")

    # 构造要生成的文件绝对路径
    prepare_path = p.joinpath(p.parent.parent, 'output_dir')
    try:

        Path.mkdir(prepare_path)

        logger.info(f"Create a new directory : {prepare_path}")
    except FileExistsError:
        pass
    output_path_contain_stem = p.joinpath(prepare_path, p.stem)
    output_dir = prepare_path
    return output_path_contain_stem, output_dir

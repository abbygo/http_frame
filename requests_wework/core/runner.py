import inspect
import re
import sys
import uuid
from pathlib import Path
from typing import NoReturn, Dict, Text

import yaml
from loguru import logger
from sentry_sdk import capture_exception

from requests_wework.action.api_action import api_action
from requests_wework.core.models import TStep, VariablesMapping, TestCase, TConfig
from requests_wework.core.testcase import Step, Config

from functools import wraps


def print_log(fun):
    '''
    打印日志
    :param fun: 函数
    :return:
    '''

    @wraps(fun)
    def wrapper(*args, **kargs):
        case_id = str(uuid.uuid4())
        logger.info(
            f"Start to run testcase, TestCase ID: {case_id}"
        )

        result = fun(*args, **kargs)
        logger.info(
            f"End of use testcase run, TestCase ID: {case_id}"
        )
        return result

    return wrapper


class PareStep(object):
    config: Config
    __case_id: Text = ""
    __session_variables: VariablesMapping = {}

    def __init_data_structure(self, step: Step) -> NoReturn:
        '''
        初始化数据的结构体
        :param step:
        :return:
        '''
        # 获取config中的数据
        self.__config = self.config.perform()
        self.step = step

        self.data_entries: Dict = {"depend": ["requests"]}
        self.testcase_name = ''

        self.__teststeps = {}
        self.__case_id = self.__case_id or str(uuid.uuid4())

        config_variables = self.__config.variables

        config_variables.update(self.__session_variables)

        self.init_data()

    def init_data(self):
        '''
        构造数据

        eg:data_entries数据结构：

        {
    "depend": [
        "requests"
    ],
    "test_gettoken": {
        "run_request": {
            "method": "GET",
            "url": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            "params": {
                "corpid": "wwf2dbb0a93f2eac33",

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
        '''
        tstep: TStep = self.step.perform()
        # 获取测试用例的名称；eg:test_gettoken
        name = inspect.stack()[4].function

        if name.startswith("test_"):

            # 构造case_name
            tstep.case_name = name
            self.testcase_name = name
        else:
            logger.exception('not found test_开头的函数')
            sys.exit(1)

        # eg: "def_gettoken": {"run_request": {}}
        self.__teststeps[tstep.case_name] = tstep.case_value
        # eg:{"run_request": {}}
        self.run_request_entries: Dict = self.__teststeps[tstep.case_name].get(
            tstep.case_key
        )
        if tstep.request.method:
            self.run_request_entries["method"] = tstep.request.method
        else:
            logger.exception('not found method')
            sys.exit(1)
        if tstep.request.url:
            self.run_request_entries["url"] = tstep.request.url
        else:
            logger.exception('not found url')
            sys.exit(1)
        if tstep.request.params:
            self.run_request_entries["params"] = tstep.request.params
        else:
            pass

        if tstep.request.headers:
            self.run_request_entries["headers"] = tstep.request.headers
        else:
            pass
        if tstep.request.req_json:
            self.run_request_entries["json"] = tstep.request.req_json
        else:
            pass
        if tstep.request.data:
            self.run_request_entries["data"] = tstep.request.data
        else:
            pass
        if tstep.request.cookies:
            self.run_request_entries["cookies"] = tstep.request.cookies
        else:
            pass
        if tstep.validators:
            self.run_request_entries["validate"] = tstep.validators
        else:
            pass
        if tstep.extract:
            self.run_request_entries["extractors"] = tstep.extract
        else:
            pass

        self.data_entries.update(self.__teststeps)

    def with_variables(self, variables: VariablesMapping) -> "PareStep":
        self.__session_variables = variables
        return self

    def find_env_file(self, path_obj, i=0):
        '''
        查找env文件
        :param path_obj: Path的实例
        :param i: i 表示第几级父类
        :return:
        '''

        # 找到了文件这个变量变为TRue
        find_file = False
        # 循环迭代文件夹，i 表示第级父类
        for path in path_obj.parents[i].iterdir():
            if Path.is_file(path):
                if str(path).endswith('env.yml'):
                    find_file = True

                    env_path = path
                    return env_path
        if find_file == False:
            i += 1
            # 最多找5层目录
            if i <= 5:
                return self.find_env_file(path_obj, i)
            else:
                logger.error('Maximum number of iterations exceeded 5,not found env.yml')
                sys.exit(1)

    def read_env_file(self, env_path, tconfig: TConfig):
        with open(env_path, encoding='utf-8') as f:

            '''
            读取env文件内容
            '''
            content = yaml.safe_load(f)
            # 替换base_url
            function_regex_compile = re.compile(r"\$\{(\w+)\((\w+)\)\}")

            try:
                result_list: list = function_regex_compile.findall(tconfig.base_url)
                # result_list==>[('ENV','base_url')]
                if result_list:
                    if result_list[0][0] == 'ENV':
                        if content.get(result_list[0][1]):

                            tconfig.base_url = content.get(result_list[0][1])
                            return content
                        else:
                            logger.error(f'in env.yaml file not found {result_list[0][1]}')
                            sys.exit(1)

            except TypeError as ex:
                capture_exception(ex)
                return []

    def load_project_meta(self, tconfig: TConfig):
        # 获取正在执行的用例名称
        filename = inspect.stack()[2].filename
        # C:\Users\lnz\PycharmProjects\http_homework\requests_wework\testcases\test_tag_newpy.py
        p = Path(filename)
        env_path = self.find_env_file(p)
        self.read_env_file(env_path, tconfig)

    @print_log
    def start(self, step: Step):
        '''
        入口
        :param step:
        eg:
        包含多个对象： def __init__(
            self,
            step_context: Union[
                StepRequestValidation, RequestWithOptionalArgs, RunRequest,
            ],
        :return:
        '''
        try:

            self.__init_data_structure(step)
            # 加载env.yaml中的数据
            self.load_project_meta(self.__config)
            # 组装测试对象
            testcase_obj = TestCase(config=self.__config, teststeps=self.data_entries)
            # 实例化api类
            api_obj = api_action(self.data_entries)

            # 调用运行方法
            api_obj.run_fun(self.testcase_name, testcase_obj)


        except:
            raise

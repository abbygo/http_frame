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
from requests_wework.core.content import PyContent
from requests_wework.core.models import TStep, VariablesMapping, TestCase, TConfig
from requests_wework.core.testcase import Step, Config


class PareStep(object):
    config: Config
    __case_id: Text = ""
    __session_variables: VariablesMapping = {}
    case_name_list = []

    def __init_tests__(self, step: Step) -> NoReturn:
        self.__config = self.config.perform()
        self.step = step

        self.data_entries: Dict = {"depend": ["requests"]}
        self.case_name_list = []
        # for step in self.teststeps:
        self.__teststeps = {}
        self.__case_id = self.__case_id or str(uuid.uuid4())
        # parse config name
        config_variables = self.__config.variables

        config_variables.update(self.__session_variables)
        # self.__config.name = parse_data(
        #     self.__config.name, config_variables, self.__project_meta.functions
        # )
        logger.info(
            f"Start to run testcase: {self.__config.name}, TestCase ID: {self.__case_id}"
        )

        self.init_data()

    def init_data(self):
        tstep: TStep = self.step.perform()
        # 获取测试用例的名称；eg:test_gettoken
        name = inspect.stack()[3].function

        if name.startswith("test_"):

            # 构造case_name
            tstep.case_name = name
            self.case_name_list.append(name)
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

    def load_project_meta(self,tconfig:TConfig):
        # 获取正在执行的用例名称
        filename = inspect.stack()[2].filename
        # C:\Users\lnz\PycharmProjects\http_homework\requests_wework\testcases\test_tag_newpy.py
        p = Path(filename)
        # 查找env文件
        env_path=''
        def find_env_file(i=0):
            # 找到了文件这个变量变为TRue
            find_file = False
            # 循环迭代文件夹，i 表示第级父类
            for path in p.parents[i].iterdir():
                if Path.is_file(path):
                    if str(path).endswith('env.yml'):
                        find_file = True
                        nonlocal env_path
                        env_path=path
                        return env_path
            if find_file == False:
                i += 1
                # 最多找5层目录
                if i <= 5:
                    find_env_file(i)
                else:
                    logger.error('not found env.yml')
                    sys.exit(1)

        find_env_file()
        with open(env_path,encoding='utf-8') as f:

            '''
            读取env文件内容
            '''
            content=yaml.safe_load(f)
            # 替换base_url
            function_regex_compile = re.compile(r"\$\{(\w+)\((\w+)\)\}")

            try:
                result_list:list=function_regex_compile.findall(tconfig.base_url)
                # result_list==>[('ENV','base_url')]
                if result_list:
                    if result_list[0][0]=='ENV':
                        if content.get(result_list[0][1]):

                            tconfig.base_url = content.get(result_list[0][1])
                            return content
                        else:
                            logger.error(f'in env.yaml file not found {result_list[0][1]}')
                            sys.exit(1)

            except TypeError as ex:
                capture_exception(ex)
                return []


    def start(self, step):
        try:

            self.__init_tests__(step)
            self.load_project_meta(self.__config)
            testcase_obj = TestCase(config=self.__config, teststeps=self.data_entries)

            content = PyContent(self.data_entries)
            expression = api_action(content)

            for fun_name in self.case_name_list:
                res = expression.run_fun(fun_name, testcase_obj)

        except:
            raise

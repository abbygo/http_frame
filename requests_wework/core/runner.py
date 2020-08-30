import inspect
import uuid
from typing import NoReturn, Dict, Text

from loguru import logger

from requests_wework.action.api_action import api_action
from requests_wework.core.content import PyContent
from requests_wework.core.models import TSimpleStep, VariablesMapping, TestCase
from requests_wework.core.testcase import Step, Config


class PareStep(object):
    config: Config
    __case_id: Text = ""
    __session_variables: VariablesMapping = {}
    case_name_list = []

    def __init_tests__(self, step: Step, param: Dict = None) -> NoReturn:
        self.__config = self.config.perform()
        self.step = step

        self.data_entries: Dict = {"depend": ["requests"]}
        self.case_name_list = []
        # for step in self.teststeps:
        self.__teststeps = {}
        self.__case_id = self.__case_id or str(uuid.uuid4())
        # parse config name
        config_variables = self.__config.variables
        if param:
            config_variables.update(param)
        config_variables.update(self.__session_variables)
        # self.__config.name = parse_data(
        #     self.__config.name, config_variables, self.__project_meta.functions
        # )
        logger.info(
            f"Start to run testcase: {self.__config.name}, TestCase ID: {self.__case_id}"
        )

        self.init_data()

    def init_data(self):
        tSimpleStep: TSimpleStep = self.step.perform()
        # 获取测试用例的名称；eg:test_gettoken
        name = inspect.stack()[3].function
        try:
            # todo
            if name.startswith("test_"):
                # 去掉函数前缀test_,获取真实的函数名
                tSimpleStep.case_name = f"def_{name[5:]}"
                self.case_name_list.append(name[5:])
        except:
            raise

        # eg: "def_gettoken": {"run_request": {}}
        self.__teststeps[tSimpleStep.case_name] = tSimpleStep.case_value
        # eg:{"run_request": {}}
        self.run_request_entries: Dict = self.__teststeps[tSimpleStep.case_name].get(
            tSimpleStep.case_key
        )
        if tSimpleStep.request.method:
            self.run_request_entries["method"] = tSimpleStep.request.method
        else:
            #     todo
            pass
        if tSimpleStep.request.url:
            self.run_request_entries["url"] = tSimpleStep.request.url
        else:
            pass
        if tSimpleStep.request.params:
            self.run_request_entries["params"] = tSimpleStep.request.params
        else:
            pass

        if tSimpleStep.request.headers:
            self.run_request_entries["headers"] = tSimpleStep.request.headers
        else:
            pass
        if tSimpleStep.request.req_json:
            self.run_request_entries["json"] = tSimpleStep.request.req_json
        else:
            pass
        if tSimpleStep.request.data:
            self.run_request_entries["data"] = tSimpleStep.request.data
        else:
            pass
        if tSimpleStep.request.cookies:
            self.run_request_entries["cookies"] = tSimpleStep.request.cookies
        else:
            pass
        if tSimpleStep.validators:
            self.run_request_entries["validate"] = tSimpleStep.validators
        else:
            pass
        if tSimpleStep.extract:
            self.run_request_entries["extractors"] = tSimpleStep.extract
        else:
            pass

        self.data_entries.update(self.__teststeps)

    def with_variables(self, variables: VariablesMapping) -> "PareStep":
        self.__session_variables = variables
        return self

    def start(self, step):
        try:
            self.__init_tests__(step)

            testcase_obj = TestCase(config=self.__config, teststeps=self.data_entries)

            content = PyContent(self.data_entries)
            expression = api_action(content)

            for fun_name in self.case_name_list:
                res = expression.run_fun(fun_name, testcase_obj)

        except:
            raise

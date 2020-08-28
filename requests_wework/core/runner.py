import uuid
from typing import List, NoReturn, Dict

from requests_wework.action.api_action import api_action
from requests_wework.core.content import PyContent
from requests_wework.core.models import TSimpleStep
from requests_wework.core.testcase import Step


class PareStep(object):
    # config: Config
    teststeps: List[Step]

    def __init_tests__(self) -> NoReturn:
        # self.__config = self.config.perform()
        self.data_entries: Dict = {"depend": ["requests"]}
        self.case_name_list = []
        for step in self.teststeps:
            self.__teststeps = {}
            tSimpleStep: TSimpleStep = step.perform()
            # eg: "def_gettoken": {"run_request": {}}
            self.__teststeps[tSimpleStep.case_name] = tSimpleStep.case_value
            # eg:{"run_request": {}}
            self.run_request_entries: Dict = self.__teststeps[
                tSimpleStep.case_name
            ].get(tSimpleStep.case_key)
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
            if tSimpleStep.case_name.startswith("def_"):
                # 去掉函数前缀test_,获取真实的函数名
                name = tSimpleStep.case_name[4:]
                self.case_name_list.append(name)
            self.data_entries.update(self.__teststeps)

    def test_start(self):
        self.__init_tests__()
        print(self.data_entries)
        content = PyContent(self.data_entries)
        # expression = api_action(content)
        # for fun_name in self.case_name_list:
        #     res = expression.run_fun(fun_name, self.data_entries)
        #     print(res)


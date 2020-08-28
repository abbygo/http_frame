"""
要解决的问题，容易把key忘记，写错了
需要链式的调用出来内容
"""

from typing import Text, Dict, Union, List, Any

from requests_wework.core.models import TSimpleStep, TRequest, MethodEnum


Headers = Dict[Text, Text]
Cookies = Dict[Text, Text]
Verify = bool
Export = List[Text]
VariablesMapping = Dict[Text, Any]
Hooks = List[Union[Text, Dict[Text, Text]]]
Validators = List[Dict]


class SimpleStep:
    def __init__(self, case_name: Text):
        self.__step_context = TSimpleStep(case_name=case_name)

    def post(self, url: Text):
        self.__step_context.request = TRequest(method=MethodEnum.POST, url=url)
        return RequestWithOptionalArgs(self.__step_context)

    def get(self, url: Text):
        self.__step_context.request = TRequest(method=MethodEnum.GET, url=url)
        return RequestWithOptionalArgs(self.__step_context)


class StepRequestValidation(object):
    def __init__(self, step_context: TSimpleStep):
        self.__step_context = step_context

    def assert_equal(
        self, jmes_path: Text, expected_value: Any
    ) -> "StepRequestValidation":
        self.__step_context.validators.append(
            {"eq": [jmes_path, expected_value]}
        )
        return self

    def assert_not_equal(
        self, jmes_path: Text, expected_value: Any
    ) -> "StepRequestValidation":
        self.__step_context.validators.append(
            {"not_equal": [jmes_path, expected_value]}
        )
        return self

    def perform(self) -> TSimpleStep:
        return self.__step_context


class RequestWithOptionalArgs(object):
    def __init__(self, step_context: TSimpleStep):
        self.__step_context = step_context

    def with_params(self, **params) -> "RequestWithOptionalArgs":
        self.__step_context.request.params.update(params)
        return self

    def with_headers(self, **headers) -> "RequestWithOptionalArgs":
        self.__step_context.request.headers.update(headers)
        return self

    def with_data(self, data) -> "RequestWithOptionalArgs":
        self.__step_context.request.data = data
        return self

    def with_json(self, req_json) -> "RequestWithOptionalArgs":
        self.__step_context.request.req_json = req_json
        return self

    def set_timeout(self, timeout: float) -> "RequestWithOptionalArgs":
        self.__step_context.request.timeout = timeout
        return self

    def set_verify(self, verify: bool) -> "RequestWithOptionalArgs":
        self.__step_context.request.verify = verify
        return self

    def set_allow_redirects(self, allow_redirects: bool) -> "RequestWithOptionalArgs":
        self.__step_context.request.allow_redirects = allow_redirects
        return self

    def upload(self, **file_info) -> "RequestWithOptionalArgs":
        self.__step_context.request.upload.update(file_info)
        return self

    def teardown_hook(
        self, hook: Text, assign_var_name: Text = None
    ) -> "RequestWithOptionalArgs":
        if assign_var_name:
            self.__step_context.teardown_hooks.append({assign_var_name: hook})
        else:
            self.__step_context.teardown_hooks.append(hook)

        return self

    # def extract(self) -> StepRequestExtraction:
    #     return StepRequestExtraction(self.__step_context)

    def validate(self) -> StepRequestValidation:
        return StepRequestValidation(self.__step_context)

    def perform(self) -> TSimpleStep:
        return self.__step_context


class Step(object):
    def __init__(
        self,
        step_context: Union[
            StepRequestValidation, RequestWithOptionalArgs, SimpleStep,
        ],
    ):
        self.__step_context = step_context.perform()

    @property
    def request(self) -> TRequest:
        return self.__step_context.request

    # @property
    # def testcase(self) -> TestCase:
    #     return self.__step_context.testcase

    def perform(self) -> TSimpleStep:
        return self.__step_context

from enum import Enum
from typing import Text, Dict, Union, List, Any



Headers = Dict[Text, Text]
Cookies = Dict[Text, Text]
Verify = bool
Export = List[Text]
VariablesMapping = Dict[Text, Any]
Hooks = List[Union[Text, Dict[Text, Text]]]
Validators = List[Dict]

from pydantic import BaseModel, Field
class MethodEnum(Text, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"


class TRequest(BaseModel):
    method: Text
    url: Text
    params: Dict[Text, Text] = {}
    headers: Headers = {}
    req_json: Union[Dict, List, Text] = Field(None, alias="json")
    data: Union[Text, Dict[Text, Any]] = None
    cookies: Cookies = {}
    timeout: float = 120
    allow_redirects: bool = True
    verify: Verify = False
    upload: Dict = {}  # used for upload files


class TSimpleStep(BaseModel):
    case_name: Text
    case_key:Text= "run_request"
    case_value: Dict = {case_key: {}}
    case_header: Dict = {"depend": [
        "requests"]}
    request: Union[TRequest, None] = None
    setup_hooks: Hooks = []
    teardown_hooks: Hooks = []
    # used to extract request's response field
    extract: VariablesMapping = {}
    # used to export session variables from referenced testcase
    export: Export = []
    validators: Validators = Field([], alias="validate")
    validate_script: List[Text] = []


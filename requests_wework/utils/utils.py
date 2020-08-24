#abby
import json
from jsonpath import jsonpath
class Utils:
    @classmethod
    def jsonpath(cls,json_object,expr):
        return jsonpath(json_object,expr)
import builtins
import re
from typing import Text, Callable

from httprunner import loader

from requests_wework.core import exceptions
from requests_wework.core.models import FunctionsMapping
from requests_wework.har2ncase import utils

absolute_http_url_regexp = re.compile(r"^https?://", re.I)


def get_mapping_function(
        function_name: Text, functions_mapping: FunctionsMapping
) -> Callable:
    """ get function from functions_mapping,
        if not found, then try to check if builtin function.

    Args:
        function_name (str): function name
        functions_mapping (dict): functions mapping

    Returns:
        mapping function object.

    Raises:
        exceptions.FunctionNotFound: function is neither defined in debugtalk.py nor builtin.

    """
    if function_name in functions_mapping:
        return functions_mapping[function_name]

    elif function_name in ["parameterize", "P"]:
        return loader.load_csv_file

    elif function_name in ["environ", "ENV"]:
        return utils.get_os_environ

    elif function_name in ["multipart_encoder", "multipart_content_type"]:
        # extension for upload test
        from httprunner.ext import uploader

        return getattr(uploader, function_name)

    try:
        # check if HttpRunner builtin functions
        built_in_functions = loader.load_builtin_functions()
        return built_in_functions[function_name]
    except KeyError:
        pass

    try:
        # check if Python builtin functions
        return getattr(builtins, function_name)
    except AttributeError:
        pass

    raise exceptions.FunctionNotFound(f"{function_name} is not found.")


def build_url(base_url, path):
    """ prepend url with base_url unless it's already an absolute URL """
    if absolute_http_url_regexp.match(path):
        return path
    elif base_url:
        return "{}/{}".format(base_url.rstrip("/"), path.lstrip("/"))
    else:
        raise exceptions.ParamsError("base url missed!")

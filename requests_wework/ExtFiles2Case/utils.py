import os
from queue import Queue
from urllib.parse import unquote

from requests_wework.core import exceptions


def convert_list_to_dict(origin_list):
    """ convert HAR data list to mapping
    提取参数转化为字典格式

    Args:
        origin_list (list)
            [
                {"name": "v", "value": "1"},
                {"key": "w", "value": "2"}
            ]

    Returns:
        dict:
            {"v": "1", "w": "2"}

    """
    return {item.get("name", item.get('key')): item.get("value") for item in origin_list}




def convert_x_www_form_urlencoded_to_dict(post_data):
    """ convert x_www_form_urlencoded data to dict
       转换数据为字典格式

    Args:
        post_data (str): a=1&b=2

    Returns:
        dict: {"a":1, "b":2}

    """
    if isinstance(post_data, str):
        converted_dict = {}
        for k_v in post_data.split("&"):
            try:
                key, value = k_v.split("=")
            except ValueError:
                raise Exception(
                    "Invalid x_www_form_urlencoded data format: {}".format(post_data)
                )
            converted_dict[key] = unquote(value)
        return converted_dict
    else:
        return post_data
def is_support_multiprocessing() -> bool:
    try:
        Queue()
        return True
    except (ImportError, OSError):
        # system that does not support semaphores(dependency of multiprocessing), like Android termux
        return False
def get_os_environ(variable_name):
    """ get value of environment variable.

    Args:
        variable_name(str): variable name

    Returns:
        value of environment variable.

    Raises:
        exceptions.EnvNotFound: If environment variable not found.

    """
    try:
        return os.environ[variable_name]
    except KeyError:
        raise exceptions.EnvNotFound(variable_name)

def omit_long_data(body, omit_len=512):
    """ omit too long str/bytes
    """
    if not isinstance(body, (str, bytes)):
        return body

    body_len = len(body)
    if body_len <= omit_len:
        return body

    omitted_body = body[0:omit_len]

    appendix_str = f" ... OMITTED {body_len - omit_len} CHARACTORS ..."
    if isinstance(body, bytes):
        appendix_str = appendix_str.encode("utf-8")

    return omitted_body + appendix_str
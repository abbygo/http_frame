from urllib.parse import unquote

def convert_list_to_dict(origin_list):
    """ convert HAR data list to mapping
    提取参数转化为字典格式

    Args:
        origin_list (list)
            [
                {"name": "v", "value": "1"},
                {"name": "w", "value": "2"}
            ]

    Returns:
        dict:
            {"v": "1", "w": "2"}

    """
    return {item["name"]: item.get("value") for item in origin_list}



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

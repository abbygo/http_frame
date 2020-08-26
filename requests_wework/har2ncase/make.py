from pathlib import Path

import jinja2
import yaml
from loguru import logger


def pre_case_content(data, file_name, class_name, open_file_name):
    '''
    解析yaml中的内容,为py文件的内容做准备
    类名，方法名，调用的文件名
    :param data:
    :param file_name:
    :return:
    '''

    fun_list = []
    for command_name, command_content in data.items():
        # 函数的命名规则都要一个前缀来表面是函数，def_
        if command_name.startswith('def_'):
            # 去掉函数前缀def_,替换为test_开头的方法，便于pytest识别
            fun_name = command_name.replace('def_', 'test_')
            fun_list.append(fun_name)
    # 构造类名
    class_name = f"Test_{class_name}"
    return gen_py_testcase(fun_list, file_name, class_name, open_file_name)


def gen_py_testcase(fun_list, file_name, class_name, open_file_name):
    '''
    生成测试用例文件
    :param fun_list: 方法名
    :param file_name: 需要新产生的文件名
    :param class_name: 需要新产生的类名
    :return:
    '''
    logger.info("testcase to py format.")
    __TEMPLATE__ = jinja2.Template(
        """# NOTE: Generated By Runner v0.0.1

from requests_wework.testcases.base_case import BaseCase
class {{ class_name }}(BaseCase):
    {% for item in  fun_list %}
         def {{item}}(self):
            r = self.basecase(r"{{open_file_name}}")
    {% endfor %}

"""
    )
    data = {
        "fun_list": fun_list,
        "file_name": file_name,
        "class_name": class_name,
        "open_file_name": open_file_name
    }
    # 渲染模板
    content = __TEMPLATE__.render(data)
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Generate py testcase successfully: {}".format(file_name))


def call_gen_py_testcase(open_file_name):
    '''
    调用生成测试用例方法
    :param file_name:
    :return:
    '''
    p = Path(open_file_name)
    with open(open_file_name, encoding='utf-8') as f:
        res = yaml.safe_load(f)
        parent_path = p.joinpath(p.parent, f"test_{p.stem}.py")
        return pre_case_content(res, parent_path, p.stem, open_file_name)
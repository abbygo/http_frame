
import pytest
from requests_wework.har2ncase.core import pre_case_content, call_gen_py_testcase

'''
测试core用例
'''

@pytest.mark.parametrize('file_name', [r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\testcases\tags_test.yaml'])
def test_gen_py_testcase(file_name):
    call_gen_py_testcase(file_name)

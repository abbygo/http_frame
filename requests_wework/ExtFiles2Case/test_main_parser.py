import pytest

from requests_wework.ExtFiles2Case import HarParser
from requests_wework.ExtFiles2Case.core import PostManParser
from requests_wework.ExtFiles2Case.make import call_gen_py_testcase

'''
测试core用例
'''


@pytest.mark.parametrize('file_name',
                         [r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\testcases\tags_test.yaml'])
def test_gen_py_testcase(file_name):
    call_gen_py_testcase(file_name)


def test_gen_yaml_case():
    HarParser(r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\testcases\ge.har').gen_testcase()


def test_read_postman_content():
    res=PostManParser(r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\Har\tags_postman.json').read_content()
    print(res)
def test_read_postman_content_error():
    PostManParser(r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\Har\postman_collection.json1').read_content()

def test_make_data():
    content=PostManParser(r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\Har\postman_collection.json').read_content()

    res=PostManParser(r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\Har\postman_collection.json').prepare_entry(content)
    print(res)

def test_gen_py_by_postman():
    PostManParser(r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\Har\tags_postman.json').call_gen_python_testcase_by_postman()
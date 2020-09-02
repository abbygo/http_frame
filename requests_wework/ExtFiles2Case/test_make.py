from requests_wework.ExtFiles2Case import HarParser


def test_gen_py_testcase_no_yaml():
    res=HarParser(r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\Har\ge.har').call_gen_python_testcase()
    print(res)

def test_gen_py_testcase_by_postman():
    res=HarParser(r'C:\Users\lnz\PycharmProjects\http_homework\requests_wework\Har\ge.har').call_gen_python_testcase()
    print(res)



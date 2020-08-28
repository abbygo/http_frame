# abby
import inspect



from requests_wework.action.api_action import api_action
from requests_wework.core.content import Content


class BaseCase():
    '''
    基础测试用例
    '''

    def basecase(self, path, data: dict = None):
        '''
        基本case
        :param path: yaml文件路径
        :param data: 测试数据
        :return:
        '''
        content = Content(path)
        expression = api_action(content)
        name = inspect.stack()[1].function
        if name.startswith('test_'):
            # 去掉函数前缀test_,获取真实的函数名
            name = name[5:]
        res = expression.run_fun(name, data)
        #
        # return res



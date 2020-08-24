import re

import pytest


from requests_wework.testcases.base_case import BaseCase


class TestAddress(BaseCase):

    @pytest.mark.parametrize('userid, name, mobile',
                             [('xvtd44{0}'.format(x), 'xihn{}u'.format(x), '164%08d' % x) for x in range(1)])
    def test_create(self, userid, name, mobile):
        r=self.basecase("./address.yaml", {
            "userid": userid,
            "mobile": mobile,
            "name": name
        },startAssert=False)
        from jsonpath import jsonpath
        assert 'created' == jsonpath(r, '$.errmsg')[0]

    @pytest.mark.parametrize('userid', ['zhang13235306771'])
    def test_get(self, userid,name=None):
        r=self.basecase("./address.yaml", {
            "userid": userid,
        })
        from jsonpath import jsonpath
        if name:
            assert jsonpath(r,'$.name')[0]==name

    @pytest.mark.parametrize('userid,name', [('zhang13235306771', '小米哈')])
    def test_update_mem(self, name, userid):

        self.basecase("./address.yaml", {'name': name, 'userid': userid})

    @pytest.mark.parametrize('userid', ['zhang13235306771'])
    def test_delete_mem(self, userid):
        self.basecase("./address.yaml", {'userid': userid})

    @pytest.mark.parametrize('department_id', [1])
    def test_simplelist(self, department_id):
        self.basecase("./address.yaml", {'department_id': department_id})

    @pytest.mark.parametrize('userid, name, mobile',
                             [('xvtdm{0}'.format(x), 'xiovmg{}u'.format(x), '164%08d' % x) for x in range(1)])
    def test_all(self, userid, name, mobile):
        try:

            self.test_create(userid, name, mobile)
        except AssertionError as e:
            if "mobile existed" in e.__str__():
                re_userid = re.findall(":(.*)'$", e.__str__())[0]

                self.test_delete_mem( re_userid)
                self.test_create( userid, name, mobile)
        self.test_get(userid)
        self.test_update_mem( '小米',userid)
        self.test_get( userid, '小米')
        self.test_delete_mem( userid)

import pytest

from requests_wework.testcases.base_case import BaseCase


class TestTag(BaseCase):

    @pytest.mark.parametrize('tagname, tagid',
                             [('ux5i{0}'.format(x), '6{}'.format(x)) for x in range(1)])
    def test_create(self, tagname, tagid):
        r = self.basecase("./tag.yaml", {
            "tagname": tagname,
            "tagid": tagid
        })


    @pytest.mark.parametrize('tagid', [60])
    def test_get(self, tagid, name=None):
        r = self.basecase("./tag.yaml", {
            "tagid": tagid,
        })

    @pytest.mark.parametrize('tagid,tagname', [(60, '小米哈')])
    def test_update(self, tagid, tagname):
        r=self.basecase("./tag.yaml", {'tagid': tagid, 'tagname': tagname})
        print(r)

    # @pytest.mark.parametrize('department_id', [1])
    def test_list(self):
        self.basecase("./tag.yaml")

    # 增加标签成员
    @pytest.mark.parametrize('tagid,userlist,partylist', [(60, ['zhangs3n2', 'zhangs9n2'], [1])])
    def test_addtagusers(self, tagid, userlist, partylist):
        self.basecase("./tag.yaml", {
            'tagid': tagid, 'userlist': userlist, 'partylist': partylist
        })

    @pytest.mark.parametrize('tagid', [60])
    def test_get(self, tagid, name=None):
        r = self.basecase("./tag.yaml", {
            "tagid": tagid,
        })

    # 删除标签成员
    @pytest.mark.parametrize('tagid,userlist,partylist', [(60, ['zhangs3n2', 'zhangs9n2'], [1])])
    def test_deltagusers(self, tagid, userlist, partylist):
        self.basecase("./tag.yaml", {
            'tagid': tagid, 'userlist': userlist, 'partylist': partylist
        })

    @pytest.mark.parametrize('tagid', [60])
    def test_delete(self, tagid):
        self.basecase("./tag.yaml", {'tagid': tagid})

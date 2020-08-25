# abby
import pytest
import yaml
import requests
from requests_wework.testcases.base_case import BaseCase


class TestDepartment(BaseCase):

    # 添加部门
    @pytest.mark.parametrize('name, name_en, parentid,order',
                             [('开发{0}'.format(x), 'cip{}'.format(x), 1, 1) for x in range(1)])
    def test_create(self, name, name_en, parentid, order):
        self.basecase("./department.yaml", {'name': name, 'name_en': name_en, 'parentid': parentid,
                                            'order': order})

    # 更新部门
    @pytest.mark.parametrize('name, name_en, parentid,id', [('开发1', 'cp1', 1, 2)])
    def test_update_department(self, name, name_en, parentid, id):
        self.basecase("./department.yaml", {'name': name, 'name_en': name_en, 'parentid': parentid,
                                            'id': id})

    # 部门列表
    @pytest.mark.parametrize('id', yaml.safe_load(open('../data/department.yml', encoding='utf-8')))
    def test_depatementlist(self, id):
        self.basecase("./department.yaml", {'id': id})

    # 删除部门
    @pytest.mark.parametrize('id', [(2)])
    def test_delete_depatement(self, id):
        self.basecase("./department.yaml", {'id': id})

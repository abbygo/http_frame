from requests_wework.core.parser import get_status_code

class TestGet_status_code:
    def test_get_status_code(self):
        res=get_status_code("    pm.response.to.have.status(200);\r")
        print(res)


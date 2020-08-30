from requests_wework.core.runner import PareStep
from requests_wework.core.testcase import Step, SimpleStep, Config


class Test_Study(PareStep):
    config = (
        Config("request methods testcase: reference testcase")
        .variables(**{"tagname": "u5096i1", "tagid": "95001",})
        .base_url("https://qyapi.weixin.qq.com")
        .verify(False)
    )

    def test_gettoken(self):
        self.start(
            Step(
                SimpleStep()
                .get("/cgi-bin/gettoken")
                .with_params(
                    **{
                        "corpid": "wwf2dbb0a93f2eac33",
                        "corpsecret": "fmDbF_Ll4GPiYmrqHrqtztTTVkbG6Z1NqXjiJ-eQ1gc",
                    }
                )
                .with_headers(
                    **{
                        "Host": "qyapi.weixin.qq.com",
                        "User-Agent": "python-requests/2.24.0",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept": "*/*",
                        "Connection": "keep-alive",
                    }
                )
                .extract()
                .with_jmespath("body.access_token", "token")
                .validate()
                .assert_equal("body.errcode", 0)
                .assert_equal("status_code", 200)
            )
        )

    def test_create(self):
        self.start(
            Step(
                SimpleStep()
                .post("/cgi-bin/tag/create")
                .with_params(**{"access_token": "$(token)"})
                .with_headers(
                    **{
                        "Host": "qyapi.weixin.qq.com",
                        "User-Agent": "python-requests/2.24.0",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept": "*/*",
                        "Connection": "keep-alive",
                        "Content-Type": "application/json",
                    }
                )
                .with_json({"tagid": "$tagid", "tagname": "$tagname"},)
                .validate()
                .assert_equal("body.errcode", 0)
                .assert_equal("status_code", 200)
            )
        )

    # @pytest.mark.parametrize('tagname, tagid',
    #                          [('u34556i{0}'.format(x), '8655{}'.format(x)) for x in range(1)])
    def test_update(self):
        self.start(
            Step(
                SimpleStep()
                .post("/cgi-bin/tag/update")
                .with_params(**{"access_token": "$(token)"})
                .with_headers(
                    **{
                        "Host": "qyapi.weixin.qq.com",
                        "User-Agent": "python-requests/2.24.0",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept": "*/*",
                        "Connection": "keep-alive",
                        "Content-Type": "application/json",
                    }
                )
                .with_json({"tagid": "$tagid", "tagname": "$tagname"},)
                .validate()
                .assert_equal("body.errcode", 0)
                .assert_equal("status_code", 200)
            )
        )

    def test_delete(self):
        self.start(
            Step(
                SimpleStep()
                .get("/cgi-bin/tag/delete")
                .with_params(**{"access_token": "$(token)", "tagid": "$tagid"})
                .with_headers(
                    **{
                        "Host": "qyapi.weixin.qq.com",
                        "User-Agent": "python-requests/2.24.0",
                        "Accept-Encoding": "gzip, deflate",
                        "Accept": "*/*",
                        "Connection": "keep-alive",
                        "Content-Type": "application/json",
                    }
                )
                .validate()
                .assert_equal("body.errcode", 0)
                .assert_equal("status_code", 200)
            )
        )

    # def test_flow(self):
    #     self.test_gettoken()
    #     self.test_create()
    #     self.test_update()
    #     self.test_delete()

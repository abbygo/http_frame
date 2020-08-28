from requests_wework.core.runner import PareStep
from requests_wework.core.testcase import Step, SimpleStep


class Test_Study(PareStep):
    teststeps = [
        Step(
            SimpleStep("def_gettoken")
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
            .validate()
            .assert_equal("body.errcode", 0)
            .assert_equal("status_code", 200)
        ),
        Step(
            SimpleStep("def_create")
                .post("/cgi-bin/tag/create")
                .with_params(
                **{
                "access_token": "$(gettoken)"
            }
            )
                .with_headers(
                **{
                "Host": "qyapi.weixin.qq.com",
                "User-Agent": "python-requests/2.24.0",
                "Accept-Encoding": "gzip, deflate",
                "Accept": "*/*",
                "Connection": "keep-alive",
                "Content-Type": "application/json"
            }
            )
            .with_json(
                {
                    "tagid": '99',
                    "tagname": 'yujj'
                },
            )
                .validate()
                .assert_equal("body.errcode", 0)
                .assert_equal("status_code", 200)
        )

    ]


if __name__ == "__main__":
    Test_Study().test_start()


from requests_wework.api.base_api import BaseApi


class WeWork(BaseApi):

    def get_token(self,secret):
        corpid = 'wwf2dbb0a93f2eac33'
        corpsecret = secret
        # todo
        data=self.template(r'C:\Users\lnz\PycharmProjects\HGS\requests_wework\api\get_token.yaml',{
                "corpid": corpid,
                "corpsecret": corpsecret
            })

        return self.send(data)['access_token']



import json

from test_kbs.code.api_helper import APIHelper
from hamcrest import *
import pdb


class TestAPI(object):
    apiHelper = APIHelper('test')

    def test_get_kbs(self):
        params = {'ids': ['4009470']}
        pdb.set_trace()

        response = self.apiHelper.get("/kbs/entities/kbs/v1", params=params,
                                      headers={"Content-Type": "application/json","CLIENT-ID":"c0ec116c-fd90-11ea-84e5-acde48001122"})
        json_data = response.json()
        assert_that(response.status_code, equal_to(200), f'Problems with call: {json_data}')
        assert len(json_data['resources']) == 1, "resources length not equal to one requested"

import json
import os
import glob
import time
import pytest
from test_kbs.code.utils import split_Json, validate_dict_fields, validate_is_sorted
from test_kbs.code.api_helper import APIHelper
from hamcrest import *
from enum import Enum

# Enums for KB types


class KBTypes(Enum):
    UNKNOWN = 'Unknown'
    MONTHLY_ROLLUP = 'Monthly Rollup'
    SECURITY_UPDATES = 'Security Updates'
    ALTERNATE_CUMULATIVE = 'Alternate Cumulative'
    UPDATES = 'Updates'


class TestAPI(object):
    apiHelper = APIHelper('test')
    clientId = 'c0ec116c-fd90-11ea-84e5-acde48001122'
    entitiesPath = '/kbs/entities/kbs/v1'
    queriesPath = "/kbs/queries/kbs/v1"
    outputJsonDir = './chunkedJsonDir'
    inputJson = './kbs_input.json'
    max_limit = 100
    offset_index = 0

    @pytest.fixture
    def test_post_allKbs(self):
        '''
        step1: Fixture to split the large json into chunks and 
        POST all the kb information from those chunks.
        Validation of all imports is based on the resource count

        step2: Run the testcase

        step3:Clean up the kb from the server
        Note: KB with Null value id are ignored.
        '''
        split_Json(self.inputJson, self.outputJsonDir)

        # pre testcase record creation
        deleteEntity = []
        files = glob.glob(os.path.join(self.outputJsonDir, '*.json'))
        for each_file in files:
            with open(f"{each_file}", "r") as f1:
                data = json.load(f1)

                # creating list for post testcase cleanup
                deleteEntity.append([each["kb"]["id"]
                                    for each in data if each is not None])

                # create records for each chunks
                response = self.apiHelper.post(path=self.entitiesPath, data=json.dumps(
                    data), headers={"Content-Type": "application/json", "CLIENT-ID": self.clientId})
                response_json = response.json()

                # validate creation
                assert_that(response.status_code, equal_to(200),
                            f'Problems with call: {response_json}')
                assert_that(response_json['meta']['writes']['resources_affected'], equal_to(
                    len(data)), f'Problems with call')

        yield

        # post testcase delete the kb's from the record
        for each_chunk_ids in deleteEntity:
            params = {'ids': [each_chunk_ids]}
            del_response = self.apiHelper.delete(path=self.entitiesPath, params=params, headers={
                                                 "Content-Type": "application/json", "CLIENT-ID": self.clientId})
            time.sleep(1)
            assert_that(del_response.status_code,
                        equal_to(200), f'Problems with call')

            # check the cleanup is success
            get_response = self.apiHelper.get_resource(self.entitiesPath, params=params, headers={
                                                       "Content-Type": "application/json", "CLIENT-ID": self.clientId})
            assert len(
                get_response) == 0, f"clean up Failed : {get_response}"

    @pytest.fixture(params=[2])
    def setup_bvt_sample_data(self, request):
        '''
        Function to POST sample data with only 2 kb information 
        '''
        expectedId = {}
        count = request.param
        with open(self.inputJson, "r") as f1:
            data = json.load(f1)
        data_to_post = []
        for each_segment in data:
            if len(expectedId) == count:
                break
            expectedId[each_segment['kb']['id']] = each_segment['kb']
            data_to_post.append(each_segment)

        post_response = self.apiHelper.post(
            path=self.entitiesPath,
            data=json.dumps(data_to_post),
            headers={"Content-Type": "application/json",
                     "CLIENT-ID": self.clientId}
        )
        time.sleep(1)
        response_json = post_response.json()
        resources_affected = response_json['meta']['writes']['resources_affected']
        assert_that(post_response.status_code, equal_to(
            200), f"kb upload failed:{post_response}")
        assert_that(len(expectedId), equal_to(resources_affected),
                    f"KB  upload failed:{post_response}")

        yield expectedId

        # post testcase delete the kb's from the record
        deleteEntity = list(expectedId.keys())
        params = {'ids': [deleteEntity]}
        del_response = self.apiHelper.delete(path=self.entitiesPath, params=params, headers={
                                             "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        time.sleep(1)
        assert_that(del_response.status_code,
                    equal_to(200), f'Problems with call')

        # check the cleanup is success
        get_response = self.apiHelper.get_resource(self.entitiesPath, params=params, headers={
                                                   "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        assert len(
            get_response) == 0, f"Post-tc clean up Failed : {get_response}"

    @pytest.fixture
    def cleanUpData(self):
        '''
        Test function to delete all kbs bug is there in current offset implementation
        since the offset and limit has a bug ,current implementation of deletion involves deleting with offset always 0
        '''

        while True:
            params = {"limit": self.max_limit, "offset": self.offset_index}
            response = self.apiHelper.get_resource(path=self.queriesPath, params=params, headers={
                                                   "Content-Type": "application/json", "CLIENT-ID": self.clientId})
            delete_ids = [
                each_id for each_id in response if each_id is not None]
            if not delete_ids:
                break
            params = {"ids": delete_ids}
            expectedDeleteCount = len(delete_ids)
            response = self.apiHelper.delete(self.entitiesPath, params=params, headers={
                                             "Content-Type": "application/json", "CLIENT-ID": self.clientId})
            time.sleep(1)  # Introducing a delay of 1 second
            response_json = response.json()
            assert_that(response.status_code, equal_to(200),
                        f'Problems with call: {response_json}')
            assert_that(response_json['meta']['writes']['resources_affected'], equal_to(
                expectedDeleteCount), f'Problems with call')

    @pytest.fixture
    def query_zeroOffSet_MaxLimit(self):

        params = {"limit": self.max_limit, "offset": self.offset_index}
        response = self.apiHelper.get_resource(path=self.queriesPath, params=params, headers={
                                               "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        queryIds = [each_id for each_id in response if each_id is not None]
        yield queryIds

    @pytest.mark.testBvt
    def test_get_emptyID_kbs(self):
        '''
           Test to validate for empty kb id returns 200 OK with empty resource
        '''
        params = {'ids': ['']}  # Using non-existing ID for absence check
        response = self.apiHelper.get(self.entitiesPath, params=params,
                                      headers={"Content-Type": "application/json", "CLIENT-ID": self.clientId})
        json_data = response.json()
        assert_that(response.status_code, equal_to(200),
                    f'Problems with call: {json_data}')
        assert len(json_data['resources']
                   ) == 0, "resources length not equal to one requested"

    @pytest.mark.testBvt
    def test_get_expected_kbs(self, setup_bvt_sample_data):
        expectedEntity = list(setup_bvt_sample_data.keys())[0]
        params = {'ids': [expectedEntity]}
        response = self.apiHelper.get(self.entitiesPath, params=params,
                                      headers={"Content-Type": "application/json", "CLIENT-ID": self.clientId})
        json_data = response.json()
        assert_that(response.status_code, equal_to(200),
                    f'Problems with call: {json_data}')
        assert len(json_data['resources']
                   ) == 1, "resources length not equal to one requested"

    @pytest.mark.bug
    @pytest.mark.testBvt
    @pytest.mark.testCurrent
    @pytest.mark.parametrize("setup_bvt_sample_data", [10], indirect=True)
    def test_query_limit(self, cleanUpData, setup_bvt_sample_data):
        '''
        Test to validate the query records is as same as limit
        pre-tc:
        1. clean up the data
        2. setup sample kb information say 10
        '''
        
        # set the expected resource count and formulate params
        limit = len(setup_bvt_sample_data)
        params = {"limit": limit, "offset": self.offset_index}

        # get the resource as per the params
        response = self.apiHelper.get_resource(path=self.queriesPath, params=params, headers={
            "Content-Type": "application/json", "CLIENT-ID": self.clientId})
    
        actualResponseCount = len(response)

        # validate the received count is equal to expected count
        assert_that(actualResponseCount, equal_to(
            limit), f"expected resource count :{limit},actual resource count received :{actualResponseCount}")

    @pytest.mark.testBvt
    def test_zero_max_limit(self):
        params = {"limit": 0}
        response = self.apiHelper.get(self.queriesPath, params=params,
                                      headers={"Content-Type": "application/json", "CLIENT-ID": self.clientId})
        assert_that(response.status_code//100, equal_to(4),
                    "Expected 4xx client error status code, but received something else!!!")

    @pytest.mark.testBvt
    def test_validate_del_selective_kbs(self, setup_bvt_sample_data):
        '''
        Test to validate that only selective KB articles are deleted and the rest present
        '''
      
        deleteEntity = list(setup_bvt_sample_data.keys())[0]
        params = {'ids': [deleteEntity]}
        response = self.apiHelper.delete(path=self.entitiesPath, params=params, headers={
                                         "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        time.sleep(1)
        response_json = response.json()
        assert_that(response.status_code, equal_to(200),
                    f'Problems with delete call : {response_json}')

    @pytest.mark.bug
    @pytest.mark.testBvt
    def test_validate_kb_fields_(self, setup_bvt_sample_data):
        '''
        Test validates that the imported kb information is same as in the server
        Product bug --> NDEV-001
        '''

        # Extract the first element and its expected data
        testEntity = list(setup_bvt_sample_data.keys())

        # GET  the resource information from teh server
        params = {'ids': [testEntity]}
        actualResponse = self.apiHelper.get_resource(self.entitiesPath, params=params,
                                                     headers={"Content-Type": "application/json", "CLIENT-ID": self.clientId})

        # Validate the actual data matches the expected data
        assert len(actualResponse) == len(
            testEntity), f"kb with id {testEntity} is missing"

        for each_kb in actualResponse:
            expectedData = setup_bvt_sample_data[each_kb['id']]
            validate_dict_fields(expectedData, each_kb)
    
    @pytest.mark.bug
    @pytest.mark.testReg
    @pytest.mark.parametrize("kb_type", [KBTypes.UNKNOWN, KBTypes.MONTHLY_ROLLUP, KBTypes.SECURITY_UPDATES, KBTypes.ALTERNATE_CUMULATIVE, KBTypes.UPDATES])
    def test_filter_by_type(self, kb_type, cleanUpData, test_post_allKbs):
        '''
        Test to validate filtering and fetching resources based on kb.type
        Note : All the tests will fail because of bug w.r.t mismatch between total resources and resources listed
        '''
        filterIds = set()
        totalResource = 0
        while True:
            params = {
                "limit": self.max_limit,
                "offset": self.offset_index,
                "filter": f"kb.type:{kb_type.value}"
            }
            response = self.apiHelper.get(path=self.queriesPath, params=params, headers={
                                          "Content-Type": "application/json", "CLIENT-ID": self.clientId})
            time.sleep(1)
            response_json = response.json()
        
            totalResource = response_json["meta"]["pagination"]["total"]
            if response_json["resources"] is not None:
                filterIds = filterIds.union(set(response_json["resources"]))
            if totalResource < self.offset_index+self.max_limit:
                break
            self.offset_index = self.max_limit
        assert_that(len(filterIds), equal_to(totalResource),
                    f"Expected {len(filterIds)}  ids for filter {kb_type.value} is not same as expected count {totalResource}")
    

    @pytest.mark.testReg
    def test_filter_by_id(self, cleanUpData, setup_bvt_sample_data):
        '''
        Test to validate filtering and fetching resources based on kb.id
        Note : All the tests will fail because of bug w.r.t mismatch between total resources and resources listed
        '''

        filterIds = list(setup_bvt_sample_data.keys())[0]
        totalResource = 0

        params = {
            "limit": self.max_limit,
            "offset": self.offset_index,
            "filter": f"kb.id:{filterIds}"
        }
        response = self.apiHelper.get_resource(path=self.queriesPath, params=params, headers={
            "Content-Type": "application/json", "CLIENT-ID": self.clientId})

        assert_that(len(response), equal_to(
            1), "issue with filter,expected response 1")
        assert set(filterIds) == set(response[0]), \
            f"Expected IDs: {filterIds}, Actual IDs: {response[0]}"

    @pytest.mark.testReg
    def test_del_last5kbs(self, test_post_allKbs, query_zeroOffSet_MaxLimit):
        expectedDeleteCount = 5

        # Check if there are enough records to delete
        if (not query_zeroOffSet_MaxLimit) or (len(query_zeroOffSet_MaxLimit) < 5):
            pytest.skip(
                f"Not enough records to delete: {len(query_zeroOffSet_MaxLimit)} found")

        # Get the IDs of the last 5 records
        delete_ids = query_zeroOffSet_MaxLimit[-expectedDeleteCount:]

        # Delete the records
        params = {"ids": delete_ids}

        # Verify that the records are indeed present
        response = self.apiHelper.get_resource(self.entitiesPath, params=params, headers={
                                               "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        assert len(
            response) == expectedDeleteCount, f"get_resource returns value less than {expectedDeleteCount} : {response}"

        # Delete the records
        response = self.apiHelper.delete(self.entitiesPath, params=params, headers={
                                         "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        time.sleep(1)
        response_json = response.json()

        # Verify the delete request response
        assert_that(response.status_code, equal_to(200),
                    f'Problems with delete call: {response_json}')
        assert_that(response_json['meta']['writes']['resources_affected'], equal_to(expectedDeleteCount),
                    f'Problems with delete action, not all rows are deleted :{response_json}')

        # Verify that the records are indeed deleted
        response = self.apiHelper.get_resource(self.entitiesPath, params=params, headers={
                                               "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        assert len(
            response) == 0, f"Delete last 5 kbs failed,records still present : {response}"

        self.apiHelper.logger.info(
            f"{delete_ids} are deleted from the records")

    @pytest.mark.bug
    @pytest.mark.testReg
    @pytest.mark.parametrize("sort_order", ['|asc', '|desc'])
    def test_validate_asc_sortByID(self, test_post_allKbs, sort_order):

        # formulate the params
        params = {"limit": self.max_limit, "offset": self.offset_index,
                  "sort": f"kb.id{sort_order}"}

        # Fetch the sorted resources from API
        response = self.apiHelper.get_resource(path=self.queriesPath, params=params, headers={
                                               "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        queryIds = [each_id for each_id in response if each_id is not None]

        # validate sorting order
        if len(queryIds) >= 1:
            assert_that(validate_is_sorted(queryIds, sort_order), equal_to(
                True), f"Response is not sorted {sort_order}: {queryIds}")
        else:
            raise ValueError(f"No active records : {queryIds}")

    @pytest.mark.bug
    @pytest.mark.testReg
    @pytest.mark.parametrize("sort_order", ['|asc', '|desc'])
    def test_validate_asc_sortByPublishDate(self, test_post_allKbs, sort_order):

        # formulate the params
        params = {"limit": self.max_limit, "offset": self.offset_index,
                  "sort": f"kb.publish_date{sort_order}"}

        # Fetch the sorted resources from API
        response = self.apiHelper.get_resource(path=self.queriesPath, params=params, headers={
                                               "Content-Type": "application/json", "CLIENT-ID": self.clientId})
        queryIds = [each_id for each_id in response if each_id is not None]

        # validate sorting order
        if len(queryIds) >= 1:
            assert_that(validate_is_sorted(queryIds, sort_order), equal_to(
                True), f"Response is not sorted {sort_order}: {queryIds}")
        else:
            raise ValueError(f"No active records : {queryIds}")

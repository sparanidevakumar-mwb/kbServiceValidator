# kbServiceValidator

command Execution:

pytest test.py --html=report.html

Sample Output:
-------------------------------------------------- Generated html report: file:///Users/SParanidevakumar/Desktop/cs-hw/test*kbs/code/report.html --------------------------------------------------
===================================================================================== short test summary info =====================================================================================
FAILED test.py::TestAPI::test_query_limit[10] - AssertionError: expected resource count :10,actual resource count received :9
FAILED test.py::TestAPI::test_zero_max_limit - AssertionError: Expected 4xx client error status code, but received something else!!!
FAILED test.py::TestAPI::test_validate_kb_fields*[2] - AssertionError: Values for key 'link' do not match: https://www.catalog.update.microsoft.com/Search.aspx?q=KB4009470 !=
FAILED test.py::TestAPI::test_filter_by_type[KBTypes.UNKNOWN] - AssertionError: Expected 63 ids for filter Unknown is not same as expected count 64
FAILED test.py::TestAPI::test_filter_by_type[KBTypes.MONTHLY_ROLLUP] - AssertionError: Expected 21 ids for filter Monthly Rollup is not same as expected count 22
FAILED test.py::TestAPI::test_filter_by_type[KBTypes.SECURITY_UPDATES] - AssertionError: Expected 177 ids for filter Security Updates is not same as expected count 179
FAILED test.py::TestAPI::test_filter_by_type[KBTypes.ALTERNATE_CUMULATIVE] - AssertionError: Expected 5 ids for filter Alternate Cumulative is not same as expected count 6
FAILED test.py::TestAPI::test_filter_by_type[KBTypes.UPDATES] - AssertionError: Expected 3 ids for filter Updates is not same as expected count 4
FAILED test.py::TestAPI::test_validate_asc_sortByID[|asc] - AssertionError: Response is not sorted |asc: ['4052231', '4041688', '4041691', '4038801', '4038782', '4039396', '4034661', '4034658', '4038220', '4025334', '4025339', '4022723', '4022715', '...
FAILED test.py::TestAPI::test_validate_asc_sortByID[|desc] - AssertionError: Response is not sorted |desc: ['4052231', '4041688', '4041691', '4038801', '4038782', '4039396', '4034661', '4034658', '4038220', '4025334', '4025339', '4022723', '4022715', ...
FAILED test.py::TestAPI::test_validate_asc_sortByPublishDate[|asc] - AssertionError: Response is not sorted |asc: ['4052231', '4041688', '4041691', '4038801', '4038782', '4039396', '4034661', '4034658', '4038220', '4025334', '4025339', '4022723', '4022715', '...
FAILED test.py::TestAPI::test_validate_asc_sortByPublishDate[|desc] - AssertionError: Response is not sorted |desc: ['4052231', '4041688', '4041691', '4038801', '4038782', '4039396', '4034661', '4034658', '4038220', '4025334', '4025339', '4022723', '4022715', ...
====================================================================== 12 failed, 5 passed, 17 warnings in 185.20s (0:03:05) ======================================================================
➜ code git:(feature/csUpdatedTests) ✗

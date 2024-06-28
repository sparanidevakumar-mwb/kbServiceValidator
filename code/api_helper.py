import requests
import yaml
import os
from requests.auth import HTTPBasicAuth
import logging
import copy


class BadStatusCode(Exception):
    """
    Represents an exception due to the API returning a non-successful HTTP status code
    """

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __str__(self):
        return "BadStatusCode: %d = %s" % (self.status_code, self.message)


class BadResultFormat(Exception):
    """
    Represents an exception due to the API returning badly formed results
    """

    def __init__(self, result):
        self.result = result

    def __str__(self):
        return "BadResultFormat: %s" % (self.result)


class APIErrors(Exception):
    """
    Represents an exception due to the API returning errors
    """

    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        return "APIErrors: %s" % (self.errors)


class APIHelper(object):
    """
    Helper to make api calls.
    """

    def __init__(self, service, timeout=30, verify=True, profile=None, session=False):
        self.service = service
        self.logger = logging.getLogger()

        env = os.environ.get('env')
        path = "config/api.yml".format(env)

        self.logger.debug("api_helper using {}".format(path))

        stream = open(path, 'r')
        try:
            self.config = yaml.safe_load(stream)[service]
        except KeyError as e:
            logging.exception(e.message)
            return

        if profile is None:
            self.auth = HTTPBasicAuth(self.config['auth']['username'],
                self.config['auth']['password']) if 'auth' in self.config.keys() else None
        else:
            self.auth = HTTPBasicAuth(self.config['auth'][profile]['username'],
                self.config['auth'][profile]['password']) if 'auth' in self.config.keys() and profile in self.config['auth'].keys() else None

        service_override_key = "%s_OVERRIDE" % service.upper()
        self.verify=verify
        self.timeout = timeout
        self.base_url = os.getenv(service_override_key, self.config['base_url'])
        self.headers = self.config.get('headers')
        self.session = requests.Session() if session is True else requests

        if service_override_key in os.environ:
            self.logger.info("Overriding base_url with: {}".format(os.environ[service_override_key]))

    def get_resource(self, path=None, params=None, headers=None):
        """
        Does the basic "get" operation on the api helper that applies error checking
        :param path: the path to call
        :param params: the params to pass
        :param headers: the headers to use
        :return: the "resource" field of the response object (which may be emtpy) or None if there was an issue
        """
        self.logger.debug("Getting resource at path={} params={} headers={}".format(
            path, params, headers))
        response = self.get(path, headers=headers, params=params)

        return self.__validate_resource_response_call(response, path)

    def create_resource(self, path=None, params=None, payload=None, headers=None):
        """
        Does the basic "POST" operation on the api helper that applies error checking
        :param path: the path to call
        :param params: the params to pass
        :param payload: data to be sent
        :param headers: the headers to use
        :return: the "resource" field of the response object (which may be emtpy) or None if there was an issue
        """
        self.logger.debug("Creating resource at path={} params={} headers={} payload={}".format(
            path, params, headers, payload))
        response = self.post(
            path, data=payload, headers=headers, params=params)

        return self.__validate_resource_response_call(response, path)

    def invoke_resource(self, path=None, params=None, payload=None, headers=None):
        """
        Does the basic "POST" operation on the api helper that applies error checking
        :param path: the path to call
        :param params: the params to pass
        :param payload: data to be sent
        :param headers: the headers to use
        :return: the "resource" field of the response object (which may be emtpy) or None if there was an issue
        """
        self.logger.debug("Invoking resource at path={} params={} headers={} payload={}".format(
            path, params, headers, payload))
        response = self.post(
            path, data=payload, headers=headers, params=params)

        return self.__validate_resource_response_call(response, path)

    def delete_resource(self, path=None, params=None, headers=None):
        """
        Delete the resource
        :param path: path of request
        :param params: params of request
        :param headers: headers of request
        :param logger: logger
        :return: bool - True if successfully deleted, false otherwise
        """
        self.logger.debug("Deleting resource at path={} params={} headers={}".format(
            path, params, headers))
        response = self.delete(path, headers=headers, params=params)

        if not response.status_code / 100 == 2:
            self.logger.error("Bad response code ({}) from api url: {}{}".format(
                response.status_code, self.base_url, path))

        check = response.json()
        if check is None:
            self.logger.error("No response from api url: {}{}".format(
                self.base_url, path))
            return False

        errors = check.get('errors')
        if errors is not None and len(errors) != 0:
            self.logger.error(errors)
            return False

        return True

    def disable_auth(self):
        """
        disable basic auth header for subsequent calls
        """
        self.auth = None

    def enable_auth(self):
        """
        enable basic auth header for subsequent calls
        """
        self.auth = HTTPBasicAuth(self.config['auth']['username'],
            self.config['auth']['password']) if 'auth' in self.config.keys() else None

    def __validate_resource_response_call(self, response, original_path):
        """
        Evaluate the response as a Crowdstrike "resource" and return
        back the resources field of the response, or None if there was a problem
        :param response: the actual response from the http request
        :param original_path: the path that was requested
        :return: json/dict resource, or None if there was an error
        """
        if not response.status_code / 100 == 2:
            self.logger.error("Bad response code ({}) from api url: {}{}".format(
                response.status_code, self.base_url, original_path))

        if "application/json" != response.headers.get('content-type'):
            self.logger.error("None JSON response from api url: {}{}".format(self.base_url, original_path))
            self.logger.debug("Response content from api url: {}{} \n {}".format(self.base_url, original_path, response.content))
            return None

        check = response.json()
        errors = check.get('errors')
        if errors is not None and len(errors) != 0:
            self.logger.error(errors)
            return None

        resources = check.get('resources')
        if resources is None:
            self.logger.error("Missing resources in response: {}".format(check))
            return None

        return resources

    def _filter_password(self, data):
        """
        filter data where key is in the omit logging list
        
        omit_logging = ["password", "token", "secret"]
        
        Args:
            data: dictionary to be filtered 

        Returns:
            dictionary with value 'scrub' when key is in the omit logging list
        """

        if data is None:
            return None

        if type(data) is not dict:
            return data

        debug_data = copy.deepcopy(data)
        omit_logging = ["password", "token", "secret"]
        for k,v in debug_data.items():
            if any(s in k.lower() for s in omit_logging):
                debug_data[k] = "scrub"

        return debug_data

    def __dorequest(self, method, path, url, data, params, headers, stream, files=None, allow_redirects=True, **kwargs):
        if url is None:
            url = self.base_url
        headers = self._merge_headers(headers)
        full_url = "{}{}".format(url, path)

        debug_header = self._filter_password(headers)
        debug_data = self._filter_password(data)
        debug_param = self._filter_password(params)

        self.logger.debug("request to full_url=%s, params=%s, headers=%s, data=%s", full_url, debug_param, debug_header, debug_data)
        result = method(full_url, headers=headers, params=params, data=data,
                        auth=self.auth, timeout=self.timeout, verify=self.verify, stream=stream, files=files,
                        allow_redirects=allow_redirects, **kwargs)
        self.logger.debug("request result status_code=%d", result.status_code)
        return result

    def get(self, path, url=None, data=None, params=None, headers=None, stream=False, **kwargs):
        """
        HTTP Get request
        :param path: url
        :param params: url params
        :param headers: request headers
        :param stream: support streaming apis by providing iterator (response.iter_lines())
        :return: request response
        """
        return self.__dorequest(self.session.get, path, url, data, params, headers, stream, **kwargs)

    def head(self, path, url=None, data=None, params=None, headers=None, stream=False, **kwargs):
        """
        HTTP Head request
        :param path: url
        :param params: url params
        :param headers: request headers
        :return: request response
        """
        return self.__dorequest(self.session.head, path, url, data, params, headers, stream, **kwargs)

    def post(self, path, url=None, data=None, params=None, headers=None, stream=False, files=None,
             allow_redirects=True, **kwargs):
        """
        HTTP Post request
        :param path: url
        :param data: request body
        :param headers: request headers
        :return: request response
        """
        return self.__dorequest(self.session.post, path, url, data, params, headers, stream, files,
                                allow_redirects, **kwargs)

    def delete(self, path, url=None, data=None, params=None, headers=None, stream=False, **kwargs):
        """
        HTTP Delete request
        :param path: url
        :param headers: request headers
        :return: request response
        """
        return self.__dorequest(self.session.delete, path, url, data, params, headers, stream, **kwargs)

    def put(self, path, url=None, data=None, params=None, headers=None, stream=False, **kwargs):
        """
        HTTP Put request
        :param path: url
        :param data: request body
        :param headers: request headers
        :return: request response
        """
        return self.__dorequest(self.session.put, path, url, data, params, headers, stream, **kwargs)

    def patch(self, path, url=None, data=None, params=None, headers=None, stream=False, **kwargs):
        """
        HTTP Patch request
        :param path: url
        :param data: request body
        :param headers: request headers
        :return: request response
        """
        return self.__dorequest(self.session.patch, path, url, data, params, headers, stream, **kwargs)

    def _merge_headers(self, headers):
        if self.headers is None:
            return headers

        merged_headers = {}
        for index in range(0, len(self.headers)):
            merged_headers[self.headers[index]['key']] = self.headers[index]['value']

        merged_headers.update(headers or {})

        return merged_headers

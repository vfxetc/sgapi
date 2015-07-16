import datetime
import json
import logging
import threading

from requests import Session

from .filters import adapt_filters
from .order import adapt_order


log = logging.getLogger(__name__)


class ShotgunError(Exception):
    pass


class Shotgun(object):

    def __init__(self, base_url, script_name, api_key):
        """Construct the API client."""
        self.config = self # For API compatibility

        self.base_url = base_url
        self.api_path = '/api3/json'

        self.script_name = script_name
        self.api_key = api_key

        self.session = None

        self.records_per_page = 500 # Match the Python API.

    def call(self, method_name, method_params=None, authenticate=True):
        """Make a raw API request.

        :param str method_name: The remote method to call, e.g. ``"info"``
            or ``"read"``.
        :param dict method_params: The parameters for that method.
        :param bool authenticat: Pass authentication info along?

        :raises ShotgunError: if there is a remote error.
        :returns: the API results.

        """

        if method_name == 'info' and method_params is not None:
            raise ValueError('info takes no params')
        if method_name != 'info' and method_params is None:
            raise ValueError('%s takes params' % method_name)

        if not self.session:
            self.session = Session()
        
        params = []
        request = {
            'method_name': method_name,
            'params': params,
        }

        if authenticate:
            params.append({
                'script_name': self.script_name,
                'script_key': self.api_key, # The names differ because the Python and RPC names do differ.
            })

        if method_params is not None:
            params.append(method_params)

        # print json.dumps(request, indent=4, sort_keys=True)

        endpoint = self.base_url.rstrip('/') + '/' + self.api_path.lstrip('/')
        encoded_request = json.dumps(request, default=self._json_default)
        response_handle = self.session.post(endpoint, data=encoded_request, headers={
            'User-Agent': 'sgapi/0.1',
        })
        content_type = (response_handle.headers.get('Content-Type') or 'application/json').lower()
        if content_type.startswith('application/json') or content_type.startswith('text/javascript'):
            response = json.loads(response_handle.text)
            if response.get('exception'):
                raise ShotgunError(response.get('message', 'unknown error'))
            if response.get('results'):
                return response['results']
            else:
                return response
        else:
            return response_handle.text

    def _json_default(self, v):
        if isinstance(v, datetime.datetime):
            # TODO: timezones!
            return v.replace(microsecond=0).isoformat('T') + 'Z'
        return str(v)

    def info(self):
        """Basic ``info`` request."""
        return self.call('info', authenticate=False)

    def find_one(self, entity_type, filters, fields=None, order=None,
        filter_operator=None, retired_only=False, include_archived_projects=True
    ):
        """Same as `Shotgun's find_one <https://github.com/shotgunsoftware/python-api/wiki/Reference%3A-Methods#find_one>`_"""
        for e in self.find_iter(entity_type, filters, fields, order,
            filter_operator, 1, retired_only, 1, include_archived_projects
        ):
            return e

    def find(self, *args, **kwargs):
        """Same as `Shotgun's find <https://github.com/shotgunsoftware/python-api/wiki/Reference%3A-Methods#find>`_

        If ``threads`` is set to an integer, that many threads are used to
        make consecutive page requests in parallel.


        """
        if kwargs.get('threads'):
            return self.find_iter(*args, **kwargs)
        return list(self.find_iter(*args, **kwargs))

    def find_iter(self, *args, **kwargs):
        """Like :meth:`find`, but yields entities as they become available."""
        threads = kwargs.pop('threads', 0)
        finder = _Finder(self, *args, **kwargs)
        if threads:
            return finder.iter_async(threads)
        else:
            return finder.iter_sync()


class Future(threading.Thread):

    """Really cheap version of concurrent.futures."""

    @classmethod
    def submit(cls, func, *args, **kwargs):
        future = cls(func, args, kwargs)
        future._thread.start()
        return future

    def __init__(self, func, args=None, kwargs=None):
        self._func = func
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._thread = threading.Thread(target=self._eval)

    def _eval(self):
        try:
            self._result = self._func(*self._args, **self._kwargs)
            self._exc = None
        except Exception as e:
            self._result = None
            self._exc = e

    def result(self):
        self._thread.join()
        if self._exc:
            raise self._exc
        else:
            return self._result


class _Finder(object):

    def __init__(self, sg, entity_type, filters, fields=None, order=None,
            filter_operator=None, limit=0, retired_only=False, page=0,
            include_archived_projects=True,
            
            per_page=0 # Different from shotgun_api3 starting here.
        ):

        self.sg = sg

        # We aren't a huge fan of zero indicating defaults, but we are trying
        # to be compatible here.
        for name, value in ('page', page), ('limit', limit), ('per_page', per_page):
            if not isinstance(value, int) or value < 0:
                raise ValueError('%s must be non-negative: %r' % (name, value))
        if per_page > 500:
            raise ValueError("per_page cannot be higher than 500; %r" % per_page)

        self.base_params = {

            'type': entity_type,
            'filters': adapt_filters(filters, filter_operator),
            'return_fields': list(fields or ['id']),
            'sorts': adapt_order(order),

            # These both seem to default to the above default values on the
            # server, so it isn't actually nessesary to send them.
            'return_only': 'retired' if retired_only else 'active',
            'include_archived_projects': include_archived_projects,

        }

        self.has_limit = bool(limit)
        self.limit_remaining = limit

        self.current_page = page or 1
        self.per_page = per_page or self.sg.records_per_page

        self.entities_returned = 0

        self.done = False

    def get_next_params(self):

        params = self.base_params.copy()
        params['paging'] = {
            'current_page': self.current_page,
            'entities_per_page': self.per_page,
        }
        self.current_page += 1

        # We only need paging info if we aren't making a specific request
        params['return_paging_info'] = not (self.has_limit and self.limit_remaining <= self.per_page)

        return params

    def call(self, params=None):

        if params is None:
            params = self.get_next_params()

        # Do the call!
        res = self.sg.call('read', params)

        # print json.dumps(res, sort_keys=True, indent=4)

        try:
            entities = res['entities']
        except (KeyError, TypeError):
            # We've seen strings come back a few times; it is strange.
            log.error('malformed Shotgun response: %r' % json.dumps(res))
            raise

        self.entities_returned += len(entities)

        if self.has_limit:
            entities = entities[:self.limit_remaining]
            self.limit_remaining -= len(entities)

        if not self.done:

            # Did we get what we wanted?
            if self.has_limit and self.limit_remaining <= 0:
                self.done = True

            # Did we run out?
            elif len(entities) < self.per_page:
                self.done = True

            # Is this the end?
            elif 'paging_info' in res and res['paging_info']['entity_count'] <= self.entities_returned:
                self.done = True

        return entities

    def iter_sync(self):
        while not self.done:
            for e in self.call():
                yield e

    def iter_async(self, count=1):
        
        if count is True: # for sg.find(..., threads=True)
            count = 1
        if not isinstance(count, int) or count <= 0:
            raise ValueError('async count must be greater than 0; got %r' % count)

        futures = []
        entities = []
        while True:

            while len(futures) < count:
                params = self.get_next_params()
                futures.append(Future.submit(self.call, params))

            # We yield here so that we will have had a chance to queue up the
            # next request after we captured the results.
            
            for e in entities:
                yield e

            entities = futures.pop(0).result()
            if not entities:
                return











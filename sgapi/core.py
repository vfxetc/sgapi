import json

from requests import Session

from .filters import adapt_filters
from .order import adapt_order


class ShotgunError(Exception):
    pass




class Shotgun(object):

    def __init__(self, base_url, script_name, api_key):

        self.config = self # For API compatibility

        self.base_url = base_url
        self.api_path = '/api3/json'

        self.script_name = script_name
        self.api_key = api_key

        self.session = None

        self.records_per_page = 500 # Match the Python API.

    def call(self, method_name, method_params=None, authenticate=True):

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

        print json.dumps(request, indent=4, sort_keys=True)

        endpoint = self.base_url.rstrip('/') + '/' + self.api_path.lstrip('/')
        response_handle = self.session.post(endpoint, data=json.dumps(request), headers={
            'User-Agent': 'sgapi/0.1',
        })
        content_type = (response_handle.headers.get('Content-Type') or 'application/json').lower()
        if content_type.startswith('application/json') or content_type.startswith('text/javascript'):
            response = json.loads(response_handle.text)
            if response.get('exception'):
                raise ShotgunError(response.get('message', 'unknown error'))
            return response['results']
        else:
            return response_handle.text

    def info(self):
        return self.call('info', authenticate=False)

    def find_one(self, entity_type, filters, fields=None, order=None,
        filter_operator=None, retired_only=False, include_archived_projects=True
    ):
        for e in self.find_iter(entity_type, filters, fields, order,
            filter_operator, 1, retired_only, 1, include_archived_projects
        ):
            return e

    def find(self, *args, **kwargs):
        return list(self.find_iter(*args, **kwargs))

    def find_iter(self, entity_type, filters, fields=None, order=None,
            filter_operator=None, limit=0, retired_only=False, page=0,
            include_archived_projects=True,
            
            per_page=0 # Different from shotgun_api3 starting here.
        ):

        # We aren't a huge fan of zero indicating defaults, but we are trying
        # to be compatible here.
        for name, value in ('page', page), ('limit', limit), ('per_page', per_page):
            if not isinstance(value, int) or value < 0:
                raise ValueError('%s must be non-negative: %r' % (name, value))
        if per_page > 500:
            raise ValueError("per_page cannot be higher than 500; %r" % per_page)

        params = {

            'type': entity_type,
            'filters': adapt_filters(filters, filter_operator),
            'return_fields': fields or ['id'],
            'sorts': adapt_order(order),

            # These both seem to default to the above default values on the
            # server, so it isn't actually nessesary to send them.
            'return_only': 'retired' if retired_only else 'active',
            'include_archived_projects': include_archived_projects,

        }

        has_limit = bool(limit)
        limit_remaining = limit

        current_page = page or 1
        per_page = per_page or self.records_per_page

        entities_returned = 0

        while True:

            params['paging'] = {
                'current_page': current_page,
                'entities_per_page': per_page,
            }

            # We only need paging info if we aren't making a specific request
            params['return_paging_info'] = not (has_limit and limit_remaining <= per_page)

            # Do the call!
            res = self.call('read', params)

            # print json.dumps(res, sort_keys=True, indent=4)

            entities = res['entities']

            entities_returned += len(entities)

            if has_limit:
                entities = entities[:limit_remaining]
                limit_remaining -= len(entities)

            for e in entities:
                yield e


            # Did we get what we wanted?
            if has_limit and limit_remaining <= 0:
                return

            # Did we run out?
            if len(entities) < per_page:
                return

            # Is this the end?
            if 'paging_info' in res and res['paging_info']['entity_count'] <= entities_returned:
                return

            current_page += 1










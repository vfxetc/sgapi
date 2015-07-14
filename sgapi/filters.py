'''

There are 3 different filter syntaxes we tend to see:

1. Lists of tuples: these simple filters are lists of individual filter tuples,
   usually "and"ed together (although the Python API does take a ``filter_operator``).
   These tuples are of the form::

        (path, relation, *values)

   e.g.::

        ('id', 'is', 1234)

2. Python dicts: complex logic can be expressed via dicts. They typically
   have the form::

        {
            'filter_operator': 'all', # or 'any',
            'filters': [
                # a list of filters go here
            ],
        }

   The filters can either be of the simple tuples above, or additional dicts
   of the same form.

3. API dicts: the format that is seen by the remote API is all dicts. They
   look like::

        {
            'logical_operator': 'and', # or 'or'
            'conditions': [
                # individual filters, such as:
                {
                    'path': 'id',
                    'relation': 'is',
                    'values': [1234]
                },
                # or sub filters:
                {
                    'logical_operator': 'and',
                    'conditions': [
                        # ... and so on.
                    ]
                }
            ]
        }


Here we offer functions to adapt any of the above syntaxes into the RPC version.

'''


def adapt_filters(filters, operator=None):
    """Given any of the 3 filter dialects, translate into the remote condition syntax."""

    if isinstance(filters, dict):

        operator = filters.get('filter_operator') or filters.get('logical_operator')
        if not operator:
            raise ValueError('missing operator: %r' % operator)

        conditions = filters.get('filters') or filters.get('conditions')
        if not conditions:
            raise ValueError('missing conditions: %r' % conditions)

        return {
            'logical_operator': _adapt_operator(operator),
            'conditions': _adapt_filter_list(conditions),
        }

    else:
        return {
            'logical_operator': _adapt_operator(operator),
            'conditions': _adapt_filter_list(filters),
        }


def _adapt_operator(operator):
    try:
        return {
            None : 'and',
            'all': 'and',
            'and': 'and',
            'any': 'or',
            'or' : 'or'
        }[operator]
    except KeyError:
        raise ValueError('unknown logical operator: %r' % operator)


def _adapt_filter_list(filters):
    conditions = []
    for filter_ in filters:
        if isinstance(filter_, (list, tuple)):
            conditions.append(_adapt_simple_filter(filter_))
        else:
            conditions.append(_adapt_complex_filter(filter_))
    return conditions


def _adapt_simple_filter(filter_):
    path = filter_[0]
    relation = filter_[1]
    values = filter_[2:]
    if len(values) == 1 and isinstance(values[0], (list, tuple)):
        values = values[0]
    return {
        'path': path,
        'relation': relation,
        'values': list(values),
    }


def _adapt_complex_filter(filter_):

    # If it is nested, then we handle it elsewhere.
    if 'filters' in filter_ or 'conditions' in filter_:
        return adapt_filters(filter_)

    # Otherwise, just make sure it is already good.
    if len(filter_) != 3 or not all(k in filter_ for k in ('path', 'relation', 'values')):
        raise ValueError('invalid complex filter: %r' % filter_)
    return filter_





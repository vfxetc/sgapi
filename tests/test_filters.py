from . import *

from sgapi import filters

class TestFilters(TestCase):

    def assertRoundTrip(self, conditions):
        self.assertEqual(filters.adapt_filters(conditions), conditions)

    def test_simple_filters_1(self):
        conditions = filters.adapt_filters([('id', 'is', 123)])
        self.assertEqual(conditions,
            {
                'logical_operator': 'and',
                'conditions': [
                    {
                        'path': 'id',
                        'relation': 'is',
                        'values': [123],
                    }
                ],
            }
        )

        self.assertRoundTrip(conditions)



    def test_simple_filters_2(self):
        conditions = filters.adapt_filters([('id', 'in', [123, 456])])
        self.assertEqual(conditions,
            {
                'logical_operator': 'and',
                'conditions': [
                    {
                        'path': 'id',
                        'relation': 'in',
                        'values': [123, 456],
                    }
                ],
            }
        )
        self.assertRoundTrip(conditions)

    def test_complex_filters(self):

        conditions = filters.adapt_filters([
            ["sg_status_list", "is", "ip"],
            {
                "filter_operator": "any",
                "filters": [
                    [ "assets", "is", { "type": "Asset", "id": 9 } ],
                    [ "assets", "is", { "type": "Asset", "id": 23 } ]
                ]
            }
        ])
        self.assertEqual(conditions,
            {
                'logical_operator': 'and',
                'conditions': [
                    {
                        'path': 'sg_status_list',
                        'relation': 'is',
                        'values': ['ip'],
                    }, {
                        'logical_operator': 'or',
                        'conditions': [
                            {
                                'path': 'assets',
                                'relation': 'is',
                                'values': [{ "type": "Asset", "id": 9 }],
                            },
                            {
                                'path': 'assets',
                                'relation': 'is',
                                'values': [{ "type": "Asset", "id": 23 }],
                            }
                        ]
                    }
                ],
            }
        )
        self.assertRoundTrip(conditions)



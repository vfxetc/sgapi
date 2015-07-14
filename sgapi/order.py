
def adapt_order(order):
    if not order:
        return []

    sorts = []
    for field in order:
        field_name = field.get('field_name') or field.get('column')
        direction = field.get('direction', 'asc')
        sorts.append({
            'field_name': field_name,
            'direction': direction,
        })
    return sorts


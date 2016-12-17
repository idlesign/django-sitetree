from sitetree.toolbox import tree, item


sitetrees = [
    tree('dynamic3', items=[
        item('dynamic3_1', '/dynamic3_1_url', url_as_pattern=False),
    ]),
    tree('dynamic4', items=[
        item('dynamic4_1', '/dynamic4_1_url', url_as_pattern=False),
    ]),
]

from sitetree.utils import tree, item


sitetrees = (
    tree('books', items=[
        item('Books', '/books/', url_as_pattern=False, children=[
            item('{{ book.title }}', 'books-details', in_menu=False, in_sitetree=False),
            item('Add a book', 'books-add'),
        ])
    ]),
    tree('other', items=[
        item('Item', '/item/', url_as_pattern=False, access_guest=False)
    ]),
)

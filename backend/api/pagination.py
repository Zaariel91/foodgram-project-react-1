from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинация страниц."""
    page_size_query_param = 'limit'

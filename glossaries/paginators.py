from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'page_size': self.get_page_size(self.request),
            'current_page': self.page.number,
            'previous': self.get_previous_page_number(),
            'next': self.get_next_page_number(),
            'num_pages': self.page.paginator.num_pages,
            'results': data,
        })

    def get_previous_page_number(self):
        if self.page.has_previous():
            return self.page.previous_page_number()
        return None

    def get_next_page_number(self):
        if self.page.has_next():
            return self.page.next_page_number()
        return None

from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


class APIViewPagination(PageNumberPagination):
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


class TemplateViewPagination:
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request):
        # Get page number and page size from the request
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get(self.page_size_query_param, self.page_size)
        try:
            page_size = min(int(page_size), self.max_page_size)
        except ValueError:
            page_size = self.page_size

        # Initialize paginator with the given page size
        paginator = Paginator(queryset, page_size)

        # Get the requested page
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        # Store page and paginator for later use in pagination controls
        self.page = page
        self.paginator = paginator

        return page.object_list

    def get_paginated_context(self):
        return {
            'count': self.paginator.count,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'previous': self.get_previous_page_number(),
            'next': self.get_next_page_number(),
            'num_pages': self.paginator.num_pages,
            'results': self.page.object_list,
        }

    def get_previous_page_number(self):
        if self.page.has_previous():
            return self.page.previous_page_number()
        return None

    def get_next_page_number(self):
        if self.page.has_next():
            return self.page.next_page_number()
        return None

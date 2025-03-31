from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class that provides additional metadata in pagination response
    including total number of items and current page.
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        # Get the total number of pages for the query
        count = self.page.paginator.count
        num_pages = self.page.paginator.num_pages

        # Page information
        current_page = self.page.number
        has_next = self.page.has_next()
        has_previous = self.page.has_previous()

        # Next and previous page numbers (for UI usage even when links are null)
        next_page = current_page + 1 if has_next else None
        previous_page = current_page - 1 if has_previous else None

        return Response(
            {
                "count": count,
                "total_pages": num_pages,
                "current_page": current_page,
                "page_size": self.get_page_size(self.request),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "has_next": has_next,
                "has_previous": has_previous,
                "next_page": next_page,
                "previous_page": previous_page,
                "results": data,
            }
        )

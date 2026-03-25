"""
Custom pagination classes for the InsightBoard API.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """
    Standard pagination with configurable page size.
    Supports ?page_size= query parameter up to a max of 100.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "page_size": self.get_page_size(self.request),
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Total number of items.",
                },
                "total_pages": {
                    "type": "integer",
                    "description": "Total number of pages.",
                },
                "current_page": {
                    "type": "integer",
                    "description": "Current page number.",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of items per page.",
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "description": "URL of the next page.",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "description": "URL of the previous page.",
                },
                "results": schema,
            },
        }


class LargeResultsPagination(PageNumberPagination):
    """
    Pagination for endpoints that may return large datasets (e.g. query results).
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "page_size": self.get_page_size(self.request),
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })

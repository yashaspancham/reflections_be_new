from django.shortcuts import render
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Task
from .serializers import TaskSerializer
from rest_framework import status


class TaskPagination(PageNumberPagination):
    page_size = 35


@api_view(["GET"])
def get_tasks(request):
    try:
        tasks = Task.objects.all().order_by("-createdAt")
        paginator = TaskPagination()
        paginated_tasks = paginator.paginate_queryset(tasks, request)

        serializer = TaskSerializer(paginated_tasks, many=True)

        page_obj = paginator.page
        total_entries = page_obj.paginator.count
        total_pages = page_obj.paginator.num_pages
        current_page = page_obj.number

        return Response(
            {
                "success": True,
                "total_entries": total_entries,
                "total_pages": total_pages,
                "current_page": current_page,
                "next_page": paginator.get_next_link(),
                "prev_page": paginator.get_previous_link(),
                "tasks": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

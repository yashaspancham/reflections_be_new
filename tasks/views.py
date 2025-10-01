from django.shortcuts import render
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from .models import Task
from .serializers import TaskSerializer
from rest_framework import status
import traceback
from .utils import (
    get_tasks_completed_this_week,
    get_tasks_in_progress,
    get_tasks_due_this_week,
    get_tasks_due_this_week,
)


class TaskPagination(PageNumberPagination):
    page_size = 35


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_tasks(request):
    try:
        sort = request.query_params.get("sort", "-lastUpdated")
        search = request.query_params.get("search", "")
        status_filter = request.query_params.get("status", "")
        tasks = Task.objects.filter(user=request.user)
        if search:
            tasks = tasks.filter(description__icontains=search)
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        tasks = tasks.order_by(sort)

        paginator = TaskPagination()
        page_num = int(request.query_params.get("page", 1))
        total_entries = tasks.count()
        last_page = max(
            1, (total_entries + paginator.page_size - 1) // paginator.page_size
        )

        # clamp page number
        if page_num > last_page:
            page_num = last_page
        elif page_num < 1:
            page_num = 1

        request.GET._mutable = True
        request.GET["page"] = str(page_num)
        request.GET._mutable = False

        result_page = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(result_page, many=True)

        return Response(
            {
                "success": True,
                "total_entries": total_entries,
                "total_pages": last_page,
                "current_page": page_num,
                "next_page": paginator.get_next_link(),
                "prev_page": paginator.get_previous_link(),
                "tasks": serializer.data,
                "clamped": page_num == last_page,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_task(request):
    try:
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save(user=request.user)
            return Response(
                {"success": True, "task": TaskSerializer(task).data},
                status=status.HTTP_201_CREATED,
            )
        traceback.print_exc()
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_task(request, task_id):
    try:
        task = Task.objects.get(pk=task_id, user=request.user)

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"success": True, "task": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Task.DoesNotExist:
        return Response(
            {"success": False, "error": "Task not found or unauthorized"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        task.delete()
        return Response(
            {"success": True, "message": "Task deleted successfully"},
            status=status.HTTP_200_OK,
        )
    except Task.DoesNotExist:
        return Response(
            {"success": False, "error": "Task not found or unauthorized"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_task_stats(request):
    try:
        user = request.user

        stats = {
            "tasks_completed_this_week": get_tasks_completed_this_week(user),
            "tasks_in_progress": get_tasks_in_progress(user),
            "tasks_due_this_week": get_tasks_due_this_week(user),
            "total_tasks_completed": get_total_tasks_completed(user),
        }

        return Response(stats, status=200)
    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)

from datetime import date, timedelta
from django.utils import timezone
from .models import Task


def get_tasks_completed_this_week(user):
    try:
        today = timezone.now().date()
        # week starts on monday and ends on sunday
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return user.tasks.filter(
            status="completed", lastUpdated__date__range=(start_of_week, end_of_week)
        ).count()
    except Exception as e:
        print(f"Error in get_tasks_completed_this_week: {e}")
        return 0


def get_tasks_in_progress(user):
    try:
        return user.tasks.filter(status="in_progress").count()
    except Exception as e:
        print(f"Error in get_tasks_in_progress: {e}")
        return 0


def get_tasks_due_this_week(user):
    try:
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return user.tasks.filter(
            dueDate__range=(start_of_week, end_of_week)
        ).count()
    except Exception as e:
        print(f"Error in get_tasks_due_this_week: {e}")
        return 0


def get_total_tasks_completed(user):
    try:
        return user.tasks.filter(status="completed").count()
    except Exception as e:
        print(f"Error in get_total_tasks_completed: {e}")
        return 0
from django.db import models

# Create your models here.
class Task(models.Model):
    description = models.TextField()
    status = models.CharField(max_length=50, default="pending")
    dueDate = models.DateField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    lastUpdated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task {self.id} - {self.status}"
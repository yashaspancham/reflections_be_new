from django.db import models

class Entry(models.Model):
    entryContent = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)
    lastUpdated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Entry {self.id}"
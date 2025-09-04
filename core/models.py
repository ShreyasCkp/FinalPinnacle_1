from django.db import models
from master.models import UserCustom

class RecentActivity(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),

    ]

    user = models.ForeignKey(UserCustom, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_name} {self.action} by {self.user} at {self.timestamp}"

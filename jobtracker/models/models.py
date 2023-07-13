from django.db import models


class User(models.Model):
    id = models.IntegerField(unique=True, blank=False, primary_key=True)
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    username = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


class Task(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True
    )
    profit = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    date_start = models.DateField(
        blank=True,
        null=True
    )
    date_end = models.DateField(
        blank=True,
        null=True
    )
    spent_seconds = models.PositiveIntegerField(
        default=0
    )


class Work(models.Model):
    time_start = models.DateTimeField(
        blank=True,
        null=True
    )
    time_end = models.DateTimeField(
        blank=True,
        null=True
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='works'
    )

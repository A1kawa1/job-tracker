from django.contrib import admin
from models.models import User, Task, Work


@admin.register(User)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'username')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'date_start')


@admin.register(Work)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task', 'time_start')

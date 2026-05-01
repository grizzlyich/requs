from django.contrib import admin

from .models import Comment, Department, StatusHistory, Ticket


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ('author', 'old_status', 'new_status', 'note', 'created_at')
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'department', 'status', 'priority', 'initiator', 'assignee', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'department')
    search_fields = ('number', 'title', 'description')
    inlines = [CommentInline, StatusHistoryInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'created_at')
    search_fields = ('ticket__number', 'text')


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'old_status', 'new_status', 'created_at')
    list_filter = ('new_status',)

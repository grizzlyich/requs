from django.db.models import Q, QuerySet

from .models import StatusHistory, Ticket

MANAGER_GROUPS = {'Администратор', 'Руководитель'}
CONTROLLER_GROUPS = {'Контролёр'}


def user_group_names(user) -> set[str]:
    if not getattr(user, 'is_authenticated', False):
        return set()
    return set(user.groups.values_list('name', flat=True))


def is_manager(user) -> bool:
    return bool(getattr(user, 'is_superuser', False) or MANAGER_GROUPS.intersection(user_group_names(user)))


def is_controller(user) -> bool:
    return bool(getattr(user, 'is_superuser', False) or CONTROLLER_GROUPS.intersection(user_group_names(user)))


def get_visible_tickets(user) -> QuerySet[Ticket]:
    if not getattr(user, 'is_authenticated', False):
        return Ticket.objects.none()
    if is_manager(user):
        return Ticket.objects.select_related('department', 'initiator', 'assignee', 'controller').all()
    return Ticket.objects.select_related('department', 'initiator', 'assignee', 'controller').filter(
        Q(initiator=user) | Q(assignee=user) | Q(controller=user)
    ).distinct()


def can_view_ticket(user, ticket: Ticket) -> bool:
    if is_manager(user):
        return True
    return ticket.initiator_id == user.id or ticket.assignee_id == user.id or ticket.controller_id == user.id


def can_edit_ticket(user, ticket: Ticket) -> bool:
    if is_manager(user):
        return True
    return ticket.initiator_id == user.id or ticket.assignee_id == user.id


def record_status_change(ticket: Ticket, user, old_status: str, new_status: str, note: str = '') -> None:
    if old_status == new_status:
        return
    StatusHistory.objects.create(
        ticket=ticket,
        author=user,
        old_status=old_status,
        new_status=new_status,
        note=note,
    )

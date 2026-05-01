from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, RegistrationForm, TicketForm
from .models import Ticket
from .utils import can_edit_ticket, can_view_ticket, get_visible_tickets, is_manager, record_status_change


def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('dashboard')

    if not getattr(settings, 'ALLOW_REGISTRATION', True):
        messages.error(request, 'Самостоятельная регистрация временно отключена администратором.')
        return redirect('login')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация выполнена. Теперь вы можете создавать и отслеживать заявки.')
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def home_redirect(request: HttpRequest) -> HttpResponse:
    return redirect('dashboard')


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    tickets = get_visible_tickets(request.user)
    status_counts = {status: 0 for status, _ in Ticket.Status.choices}
    for row in tickets.values('status').annotate(total=Count('id')):
        status_counts[row['status']] = row['total']

    overdue = tickets.filter(due_date__lt=timezone.localdate()).exclude(
        status__in=[Ticket.Status.COMPLETED, Ticket.Status.REJECTED]
    )
    recent_tickets = tickets[:5]

    context = {
        'status_counts': status_counts,
        'recent_tickets': recent_tickets,
        'overdue_count': overdue.count(),
        'total_count': tickets.count(),
        'high_priority_count': tickets.filter(priority__in=[Ticket.Priority.HIGH, Ticket.Priority.CRITICAL]).count(),
    }
    return render(request, 'tickets/dashboard.html', context)


@login_required
def ticket_list(request: HttpRequest) -> HttpResponse:
    tickets = get_visible_tickets(request.user)
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    overdue_only = request.GET.get('overdue', '').strip()

    if query:
        tickets = tickets.filter(Q(number__icontains=query) | Q(title__icontains=query) | Q(description__icontains=query))
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    if overdue_only:
        tickets = tickets.filter(due_date__lt=timezone.localdate()).exclude(
            status__in=[Ticket.Status.COMPLETED, Ticket.Status.REJECTED]
        )

    return render(
        request,
        'tickets/ticket_list.html',
        {
            'tickets': tickets,
            'status_choices': Ticket.Status.choices,
            'priority_choices': Ticket.Priority.choices,
            'query': query,
            'selected_status': status,
            'selected_priority': priority,
            'overdue_only': overdue_only,
        },
    )


@login_required
def ticket_create(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.initiator = request.user
            old_status = ''
            ticket.save()
            record_status_change(ticket, request.user, old_status, ticket.status, 'Заявка создана')
            messages.success(request, f'Заявка {ticket.number} успешно создана.')
            return redirect('ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm(user=request.user)

    return render(request, 'tickets/ticket_form.html', {'form': form, 'title': 'Создание заявки'})


@login_required
def ticket_detail(request: HttpRequest, pk: int) -> HttpResponse:
    ticket = get_object_or_404(
        Ticket.objects.select_related('department', 'initiator', 'assignee', 'controller'),
        pk=pk,
    )
    if not can_view_ticket(request.user, ticket):
        raise Http404('Заявка не найдена.')

    context = {
        'ticket': ticket,
        'comment_form': CommentForm(),
        'can_edit': can_edit_ticket(request.user, ticket),
        'is_manager': is_manager(request.user),
        'status_choices': Ticket.Status.choices,
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def ticket_update(request: HttpRequest, pk: int) -> HttpResponse:
    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_edit_ticket(request.user, ticket):
        raise Http404('Заявка не найдена.')

    old_status = ticket.status
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket, user=request.user)
        if form.is_valid():
            updated_ticket = form.save()
            record_status_change(updated_ticket, request.user, old_status, updated_ticket.status, 'Статус изменён через форму редактирования')
            messages.success(request, f'Заявка {updated_ticket.number} обновлена.')
            return redirect('ticket_detail', pk=updated_ticket.pk)
    else:
        form = TicketForm(instance=ticket, user=request.user)

    return render(request, 'tickets/ticket_form.html', {'form': form, 'title': f'Редактирование {ticket.number}', 'ticket': ticket})


@login_required
def add_comment(request: HttpRequest, pk: int) -> HttpResponse:
    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_view_ticket(request.user, ticket):
        raise Http404('Заявка не найдена.')

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = request.user
        comment.save()
        messages.success(request, 'Комментарий добавлен.')
    else:
        messages.error(request, 'Не удалось добавить комментарий.')
    return redirect('ticket_detail', pk=pk)


@login_required
def change_ticket_status(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != 'POST':
        return redirect('ticket_detail', pk=pk)

    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_edit_ticket(request.user, ticket):
        raise Http404('Заявка не найдена.')

    new_status = request.POST.get('status', '')
    note = request.POST.get('note', '').strip()
    valid_statuses = {choice[0] for choice in Ticket.Status.choices}
    if new_status not in valid_statuses:
        messages.error(request, 'Некорректный статус заявки.')
        return redirect('ticket_detail', pk=pk)

    old_status = ticket.status
    ticket.status = new_status
    ticket.save(update_fields=['status', 'updated_at'])
    record_status_change(ticket, request.user, old_status, new_status, note or 'Статус изменён вручную')
    messages.success(request, f'Статус заявки {ticket.number} обновлён.')
    return redirect('ticket_detail', pk=pk)

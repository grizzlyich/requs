from django.conf import settings
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField('Название подразделения', max_length=150, unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В работе'
        ON_REVIEW = 'on_review', 'На проверке'
        COMPLETED = 'completed', 'Завершена'
        REJECTED = 'rejected', 'Отклонена'

    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        MEDIUM = 'medium', 'Средний'
        HIGH = 'high', 'Высокий'
        CRITICAL = 'critical', 'Критический'

    number = models.CharField('Номер заявки', max_length=20, unique=True, editable=False)
    title = models.CharField('Краткое название', max_length=200)
    description = models.TextField('Описание работ')
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='tickets',
        verbose_name='Подразделение',
    )
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tickets',
        verbose_name='Инициатор',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        verbose_name='Исполнитель',
        blank=True,
        null=True,
    )
    controller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='controlled_tickets',
        verbose_name='Проверяющий',
        blank=True,
        null=True,
    )
    status = models.CharField(
        'Статус', max_length=20, choices=Status.choices, default=Status.NEW
    )
    priority = models.CharField(
        'Приоритет', max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    due_date = models.DateField('Срок выполнения', blank=True, null=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.number} - {self.title}'

    @property
    def is_overdue(self) -> bool:
        return bool(
            self.due_date
            and self.due_date < timezone.localdate()
            and self.status not in {self.Status.COMPLETED, self.Status.REJECTED}
        )

    def save(self, *args, **kwargs):
        if not self.number:
            date_part = timezone.localdate().strftime('%Y%m%d')
            last_ticket = Ticket.objects.filter(number__startswith=f'REQ-{date_part}').order_by('number').last()
            sequence = 1
            if last_ticket:
                try:
                    sequence = int(last_ticket.number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    sequence = 1
            self.number = f'REQ-{date_part}-{sequence:03d}'
        super().save(*args, **kwargs)


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments', verbose_name='Заявка')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='Автор')
    text = models.TextField('Комментарий')
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'Комментарий к {self.ticket.number}'


class StatusHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history', verbose_name='Заявка')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='Автор')
    old_status = models.CharField('Предыдущий статус', max_length=20, choices=Ticket.Status.choices, blank=True)
    new_status = models.CharField('Новый статус', max_length=20, choices=Ticket.Status.choices)
    note = models.CharField('Комментарий', max_length=255, blank=True)
    created_at = models.DateTimeField('Дата изменения', auto_now_add=True)

    class Meta:
        verbose_name = 'История статусов'
        verbose_name_plural = 'История статусов'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'{self.ticket.number}: {self.old_status} -> {self.new_status}'

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Comment, Department, Ticket
from tickets.utils import record_status_change


class Command(BaseCommand):
    help = 'Создание демонстрационных пользователей и тестовых данных.'

    def handle(self, *args, **options):
        for group_name in ['Администратор', 'Руководитель', 'Сотрудник', 'Контролёр']:
            Group.objects.get_or_create(name=group_name)

        users_data = [
            ('admin_demo', 'admin12345', 'Иван', 'Администраторов', ['Администратор']),
            ('manager_demo', 'manager12345', 'Мария', 'Руководитель', ['Руководитель']),
            ('employee_demo', 'employee12345', 'Дмитрий', 'Монтажников', ['Сотрудник']),
            ('controller_demo', 'controller12345', 'Ольга', 'Контролёр', ['Контролёр']),
        ]

        created_users = {}
        for username, password, first_name, last_name, groups in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first_name, 'last_name': last_name, 'email': f'{username}@example.com'},
            )
            user.first_name = first_name
            user.last_name = last_name
            user.email = f'{username}@example.com'
            if created:
                user.set_password(password)

            if username == 'admin_demo':
                user.is_staff = True
                user.is_superuser = True

            user.save()
            for group_name in groups:
                user.groups.add(Group.objects.get(name=group_name))
            created_users[username] = user

        departments = {
            name: Department.objects.get_or_create(name=name)[0]
            for name in ['Монтажный отдел', 'Отдел контроля качества', 'Склад комплектующих']
        }

        if not Ticket.objects.exists():
            today = timezone.localdate()
            samples = [
                {
                    'title': 'Проверка и восстановление соединений на плате БУ-17',
                    'description': 'Требуется перепроверить пайку после выявленных замечаний ОТК.',
                    'department': departments['Монтажный отдел'],
                    'initiator': created_users['manager_demo'],
                    'assignee': created_users['employee_demo'],
                    'controller': created_users['controller_demo'],
                    'status': Ticket.Status.IN_PROGRESS,
                    'priority': Ticket.Priority.HIGH,
                    'due_date': today + timedelta(days=2),
                },
                {
                    'title': 'Комплектация партии кабельных сборок',
                    'description': 'Необходимо подготовить и проверить комплектность перед выдачей на монтаж.',
                    'department': departments['Склад комплектующих'],
                    'initiator': created_users['employee_demo'],
                    'assignee': created_users['employee_demo'],
                    'controller': created_users['controller_demo'],
                    'status': Ticket.Status.ON_REVIEW,
                    'priority': Ticket.Priority.MEDIUM,
                    'due_date': today + timedelta(days=1),
                },
                {
                    'title': 'Анализ причин отказа по заявке №47',
                    'description': 'Нужно подготовить краткий отчёт о причинах дефекта и предложить корректирующие действия.',
                    'department': departments['Отдел контроля качества'],
                    'initiator': created_users['manager_demo'],
                    'assignee': created_users['controller_demo'],
                    'controller': created_users['manager_demo'],
                    'status': Ticket.Status.NEW,
                    'priority': Ticket.Priority.CRITICAL,
                    'due_date': today - timedelta(days=1),
                },
            ]

            for item in samples:
                ticket = Ticket.objects.create(**item)
                record_status_change(ticket, item['initiator'], '', ticket.status, 'Начальное состояние заявки')
                Comment.objects.create(
                    ticket=ticket,
                    author=item['initiator'],
                    text='Демонстрационный комментарий для заполнения истории взаимодействия.',
                )

        self.stdout.write(self.style.SUCCESS('Демонстрационные данные успешно созданы.'))

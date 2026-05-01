from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Department, Ticket


class TicketFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='pass12345')
        self.department = Department.objects.create(name='Монтажный отдел')

    def test_login_required(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_registration_creates_employee_user(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'ivanov_i',
                'last_name': 'Иванов',
                'first_name': 'Иван',
                'email': 'ivanov@example.com',
                'password1': 'StrongPass12345',
                'password2': 'StrongPass12345',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='ivanov_i').exists())
        self.assertTrue(Group.objects.filter(name='Сотрудник').exists())
        self.assertContains(response, 'Регистрация выполнена')

    def test_ticket_creation(self):
        self.client.login(username='tester', password='pass12345')
        response = self.client.post(
            reverse('ticket_create'),
            {
                'title': 'Проверка печатной платы',
                'description': 'Необходимо провести контроль качества после пайки.',
                'department': self.department.id,
                'priority': Ticket.Priority.HIGH,
                'status': Ticket.Status.NEW,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertContains(response, 'успешно создана')

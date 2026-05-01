from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Ticket
from .utils import is_manager

User = get_user_model()


class DateInput(forms.DateInput):
    input_type = 'date'


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'title',
            'description',
            'department',
            'assignee',
            'controller',
            'priority',
            'status',
            'due_date',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'due_date': DateInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['assignee'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name', 'username')
        self.fields['controller'].queryset = User.objects.filter(is_active=True).order_by('last_name', 'first_name', 'username')
        self.fields['assignee'].label_from_instance = self.user_label
        self.fields['controller'].label_from_instance = self.user_label

        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, DateInput)):
                field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

        if user and not is_manager(user):
            self.fields['status'].disabled = True
            self.fields['status'].help_text = 'Статус меняется руководителем или через карточку заявки.'
            if not self.instance.pk:
                self.fields['status'].initial = Ticket.Status.NEW


    @staticmethod
    def user_label(user):
        full_name = user.get_full_name().strip()
        return full_name if full_name else user.username

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if self.user and not is_manager(self.user):
            if self.instance.pk:
                return self.instance.status
            return Ticket.Status.NEW
        return status


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Введите комментарий...', 'class': 'form-control'}),
        }

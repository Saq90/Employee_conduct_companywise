from django import forms
from django.forms import ModelForm, DateInput

from employee.models import Attendance, Employee
from .models import Client, Lead, Task
from django.contrib.auth import get_user_model

User = get_user_model()


class DateInput(forms.DateInput):
    input_type = 'date'


# --------------------------------------Client----------------------------------------------------
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"


# --------------------------------------Lead----------------------------------------------------
class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = "__all__"


# --------------------------------------/Lead----------------------------------------------------

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'

        # widgets = {
        #     'month': DateInput(format='%Y-%m-%d'),
        # }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to']



class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'


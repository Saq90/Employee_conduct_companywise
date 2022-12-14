from django import forms
from .models import Salary


class DateInput(forms.DateInput):
    input_type = 'date'


class SalaryForm(forms.ModelForm):
    class Meta:
        model = Salary
        fields = '__all__'

        widgets = {
            'month': DateInput(format='%Y-%m-%d'),
        }

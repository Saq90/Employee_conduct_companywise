from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

from django.views.generic import CreateView, DeleteView
from django.views.generic.base import View

from account.models import CompanyStaff
from employee.models import Employee
from .forms import LeaveDataForm
from .models import Leave

from django.views.generic import DetailView, ListView
from django.db.models import Q

def BalanceCreateView(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            balancedays = request.POST.get("balancedays")
            assign_id = request.POST.get("employee_id")
            assigned_to = Employee.objects.get(id =assign_id)
            # company_staff = CompanyStaff.objects.get(id=company_staff_id)
            # user = company_staff
            # emp = Employee.objects.get(user = user)

            Leave.objects.create(balancedays=balancedays,user=assigned_to)
            return redirect(f'/leave/balancelists/{company_id}/{company_staff_id}')

        else:
            return render(request,"leave/add-leaves-balance.html",{'assigned':Employee.objects.filter(user__company__id=company_id),'company_id':company_id, 'company_staff_id':company_staff_id})

#
# class BalanceCreateView(CreateView, LoginRequiredMixin):
#     model = Leave
#     fields = ['user', 'balancedays']
#
#     def dispatch(self, request, company_id, company_staff_id, *args, **kwargs):
#         print('Dispatch function called')
#         company_staff = CompanyStaff.objects.filter(pk=company_staff_id)
#         if company_staff.exists():
#             if company_staff.first().is_authenticated:
#                 return super().dispatch(request, company_id, company_staff_id, *args, **kwargs)
#             else:
#                 return redirect('/')
#         else:
#             return redirect('/')
#
#     def form_valid(self, form):
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)


class BalanceDetailView(DetailView, LoginRequiredMixin):
    model = Leave


def Balance_list(request,company_id, company_staff_id):
    if company_id:
        balance = Leave.objects.filter(user__user__company__id=company_id)
        context = {
            'balance': balance,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'leave/leaves-balance-list.html', context)


class BalanceRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            balance = Leave.objects.get(id=id)
            balance.delete()
            return redirect(f'/leave/balancelists/{company_id}/{company_staff_id}')


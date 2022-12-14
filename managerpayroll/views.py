from django.shortcuts import render, get_object_or_404, redirect

from account.models import CompanyStaff
from employee.models import Employee
from .models import Salary
from .forms import SalaryForm
from django.views.generic import View, DetailView, UpdateView, TemplateView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .utils import render_to_pdf
from django.http import HttpResponse
from datetime import datetime
class SalaryView(View):

    def dispatch(self, request, company_id, company_staff_id, *args,**kwargs):
        print('Dispatch function called')
        company_staff = CompanyStaff.objects.filter(pk=company_staff_id)
        if company_staff.exists():
            if company_staff.first().is_authenticated:
                return super().dispatch(request, company_id, company_staff_id, *args, **kwargs)
            else:
                return redirect('/')
        else:
            return redirect('/')
    
    def get(self, request, company_id, company_staff_id):
        if company_id:
            salary = Salary.objects.filter(manager__user__company__id=company_id)
            l = []
            for s in salary:
                l.append(s.manager.id)
            form = SalaryForm(l)
            print('form',form)
            context = {'salary': salary, 'form': form, 'company_id':company_id, 'company_staff_id':company_staff_id}
            return render(request, 'managerpayroll/manager-salary.html', context)

    
    def post(self, request, company_id, company_staff_id):
        if company_id:
            form = SalaryForm(request.POST or None)
            if request.method == 'POST':
                if form.is_valid():
                    form.save()
                    messages.info(request, "Salary was successfully created")
                return redirect(f'/managerpayroll/msalary/{company_id}/{company_staff_id}')

def SalaryDetailView(request, company_id, company_staff_id, id=None,):
    print("***********************")
    # getting the template
    salary = get_object_or_404(Salary, id=id)
    print(salary)

    context = {
            "manager":salary.manager,
            "month": salary.month,
            "basic": salary.basic,
            "da_percent": salary.da_percent,
            "hra_percent": salary.hra_percent,
            "conveyance": salary.conveyance,
            "bonuses": salary.bonuses,
            "allowance": salary.allowance,
            "medical_allowance": salary.medical_allowance,
            "tds": salary.tds,
            "esi": salary.esi,
            "providence_fund": salary.providence_fund,
            "leave": salary.leave,
            "tax": salary.tax,
            "total_earnings":salary.total_earnings,
            "total_deductions":salary.total_deductions,
            "net_pay":salary.net_pay,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

    }
    return render(request,"managerpayroll/manager-payslip.html", context)

# class SalaryDetailView(DetailView):
#     model = Salary
#     template_name = "managerpayroll/manager-payslip.html"
#
#     def get_context_data(self, company_id, company_staff_id, **kwargs):
#         context = super(SalaryDetailView, self).get_context_data(**kwargs)
#         return context
#

class SalaryRemove(View):
    def get(self, request, id):
        salary = Salary.objects.get(id=id)
        print(salary)
        salary.delete()
        messages.success(request, f"{salary} deleted successfully")
        return HttpResponseRedirect(reverse('msalary'))


class Update_salary_View(UpdateView):
    model = Salary
    fields = "__all__"
    context_object_name = "salary_update"
    template_name = 'managerpayroll/manager-salary.html'
    success_url = ("/managerpayroll/salary/")



class GeneratePdf(View):
    def get(self,request,company_id, company_staff_id,id=None,*args, **kwargs):
        print("***********************")
        # getting the template
        salary = get_object_or_404(Salary, id=id)
        print(salary)

        context = {
            "manager":salary.manager,
            "month": salary.month,
            "basic": salary.basic,
            "da_percent": salary.da_percent,
            "hra_percent": salary.hra_percent,
            "conveyance": salary.conveyance,
            "bonuses": salary.bonuses,
            "allowance": salary.allowance,
            "medical_allowance": salary.medical_allowance,
            "tds": salary.tds,
            "esi": salary.esi,
            "providence_fund": salary.providence_fund,
            "leave": salary.leave,
            "tax": salary.tax,
            "total_earnings":salary.total_earnings,
            "total_deductions":salary.total_deductions,
            "net_pay":salary.net_pay,
            'company_id': company_id,
            'company_staff_id': company_staff_id,



        }

        pdf = render_to_pdf(context)

        # rendering the template
        return HttpResponse(pdf, content_type='application/pdf')

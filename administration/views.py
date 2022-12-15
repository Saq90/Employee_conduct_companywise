import json

from django.contrib.auth import authenticate, login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.views.generic.base import View
import employee
from manager_leave.models import ManagerLeave
from manager_resign.models import ManagerResign

from manageregularization.models import MRegularization
from account.utils import custom_login_required
from .forms import AttendanceForm, EmployeeForm
from leave.models import Leave
from managers.models import Manager, ManagerAttendance, ManagerPost
from regularization.models import Regularization
from resign.models import Resign
from .models import Client, Lead, Task, notification, holiday, Asign
from django.urls import reverse
from django.contrib import messages
from django.utils.decorators import method_decorator
from employee.models import Employee, role_choices, Attendance, Post, Department, Entries
from django.db import IntegrityError
from account.models import User, CompanyStaff, Company
import sweetify
from datetime import datetime
from django.http.response import JsonResponse
from django.views.generic import DetailView, ListView
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import  check_password

# -------------------------------------all employee for admin--------------------------------
@custom_login_required
def Register_Employee_View(request,company_id, company_staff_id):
    if request.method == "POST":
        employee_first_name = request.POST['employee_first_name']
        employee_last_name = request.POST['employee_last_name']
        employee_email = request.POST['employee_email']
        employee_joining_date = request.POST['employee_joining_date']
        employee_password = request.POST['employee_password']
        employee_confirm_password = request.POST['employee_confirm_password']
        employee_id = request.POST['employee_id']
        employee_phone = request.POST['employee_phone']
        employee_salary = request.POST['employee_salary']
        employee_joining_date = datetime.strptime(employee_joining_date, '%d/%m/%Y')
        department_id = request.POST.get("id")
        employee_department = Department.objects.get(id=department_id)
        assign_id = request.POST.get("manager_id")
        employee_reports_to = Manager.objects.get(id=assign_id)

        if company_id:

            try:
                if (employee_password == employee_confirm_password):
                    user = CompanyStaff.objects.create(email=employee_email, password=employee_password,company_id=company_id)
                    user.password = make_password(user.password)
                    user.full_name = employee_first_name + ' ' + employee_last_name
                    user.is_active = True
                    user.is_employee = True
                    user.save()
                    register_employee = Employee(user=user, employee_salary=employee_salary,
                                                 employee_first_name=employee_first_name,
                                                 employee_last_name=employee_last_name, employee_email=employee_email,
                                                 employee_joining_date=employee_joining_date,
                                                 employee_id=employee_id,
                                                 employee_phone=employee_phone,
                                                 employee_department=employee_department,
                                                 employee_reports_to=employee_reports_to,
                                                 )

                    register_employee.save()
                    # messages.success(request,"Employee Registered Successfully!")
                    sweetify.success(request, 'Employee Registered Successfully!', button='Ok', timer=3000)

                else:
                    messages.error(request, " Confirm password and password does not match!")
            except IntegrityError as e:
                messages.error(request, "Email Already Registered!")

        return redirect(f'/administration/all_employee/{company_id}/{company_staff_id}')

    return render(request, 'administration/all-employees.html',{'departments':Department.objects.all()},{'reports_to':Manager.objects.all()},{'company_id':company_id, 'company_staff_id':company_staff_id})


@custom_login_required
def All_Employee_View(request, company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        employee_obj_id = data.get('employee_id', None)
        employee_obj = Employee.objects.get(pk=employee_obj_id)
        return JsonResponse(employee_obj.to_json())

    else:
        AllEmployee = Employee.objects.filter(user__company__id = company_id)
        print(AllEmployee.count())
        if AllEmployee:
            max_employee_id = Employee.objects.filter(user__company__id=company_id).order_by("-id")[0].id + 1
            departments = Department.objects.filter(company__id=company_id).only('department_name')
            reports_to = Manager.objects.filter(user__company__id=company_id).only('manager_email')

            # print(departments)
            return render(request, 'administration/all-employees.html',
                        {'Employees': AllEmployee, 'max_employee_id': max_employee_id, 'departments': departments,
                        'reports_to': reports_to, 'company_id' : company_id, 'company_staff_id':company_staff_id
                        })
        else:
            max_employee_id = "NA"
            departments = "NA"
            reports_to = "NA"
            return render(request, 'administration/all-employees.html',
                        {'Employees': AllEmployee, 'max_employee_id': max_employee_id, 'departments': departments,
                        'reports_to': reports_to, 'company_id':company_id, 'company_staff_id':company_staff_id
                        })


@login_required
def All_Employee_List_View(request):
    AllEmployee = Employee.objects.filter(employee_status="Active")
    return render(request, 'administration/employees_list.html', {'Employees': AllEmployee})


@custom_login_required
def Employee_Edit_View(request, company_id,company_staff_id):
    if company_id:
        if request.method == "GET":
            employee_id = request.GET.get('employee_id')
            employee_obj = Employee.objects.get(pk=employee_id)
            return JsonResponse(employee_obj.to_json())

        elif request.method == "POST":
            employee_models_fields_list = [f.name for f in Employee._meta.get_fields()]
            employee_models_fields_dict = {}
            employee_obj_id = request.POST.get('employee_id')
            employee_obj = Employee.objects.filter(pk=employee_obj_id)

            for key, value in request.POST.items():
                if key in employee_models_fields_list and key != 'employee_id' and key != 'id' and value is not None and len(
                        value) != 0:
                    print(key, value)
                    employee_models_fields_dict.setdefault(key, value)
            employee_obj.update(**employee_models_fields_dict)
            emp_id = request.POST.get('employee_id')

            if 'employee_image' in request.FILES:
                employee_obj = employee_obj.first()
                employee_obj.employee_image = request.FILES['employee_image']
                employee_obj.save()

            print('Employee id is-')
            print(emp_id)
            return redirect(f'/administration/all_employee/{company_id}/{company_staff_id}')



def Remove_Employee_List(request, id):
    employees = Employee.objects.get(id=id)
    User.objects.get(id=employees.user.id).delete()
    employees.delete()
    messages.success(request, "deleted successfully")
    return HttpResponseRedirect('/administration/all_employee_list')


# @login_required
def Remove_Employee(request, id,company_id,company_staff_id):
    employees_list = Employee.objects.filter(id=id)
    if employees_list.count() > 0:
        employees = employees_list.first()
        try:
            CompanyStaff.objects.get(id=employees.user.id).delete()
            print(employees)
            employees.delete()
            messages.success(request, "deleted successfully")
            return redirect(f'/administration/all_employee/{company_id}/{company_staff_id}')
        except:
            return redirect(f'/administration/all_employee/{company_id}/{company_staff_id}')
    print('hii22')
    return redirect(f'/administration/all_employee/{company_id}/{company_staff_id}')


@custom_login_required
def Update_Employees_View(request, company_id, id):
    print('0000000000')
    update_info = Employee.objects.get(id=id)
    return render(request, 'administration/all-employees.html', {'update_info': update_info})


@custom_login_required
def Register_manager_View(request,company_id, company_staff_id):
    if request.method == "POST":
        manager_first_name = request.POST['manager_first_name']
        manager_last_name = request.POST['manager_last_name']
        manager_email = request.POST['manager_email']
        manager_joining_date = request.POST['manager_joining_date']
        manager_department = request.POST['manager_department']
        manager_password = request.POST['manager_password']
        manager_confirm_password = request.POST['manager_confirm_password']
        manager_id = request.POST['manager_id']
        manager_phone = request.POST['manager_phone']
        manager_salary = request.POST['manager_salary']
        manager_joining_date = datetime.strptime(manager_joining_date, '%d/%m/%Y')
        # employee_role = Group.objects.get(name=request.POST['employee_role'])
        if company_id:
            try:
                if (manager_password == manager_confirm_password):
                    user = CompanyStaff.objects.create(email=manager_email, password=manager_password,company_id=company_id)
                    user.password = make_password(user.password)

                    user.full_name = manager_first_name + ' ' + manager_last_name
                    user.is_active = True
                    user.is_manager = True

                    user.save()
                    register_manager = Manager(user=user, manager_salary=manager_salary,
                                               manager_first_name=manager_first_name,
                                               manager_last_name=manager_last_name, manager_email=manager_email,
                                               manager_joining_date=manager_joining_date,
                                               manager_department=manager_department, manager_id=manager_id,
                                               manager_phone=manager_phone)
                    register_manager.save()
                    # messages.success(request,"Employee Registered Successfully!")
                    sweetify.success(request, 'Manager  Registered Successfully!', button='Ok', timer=3000)

                else:
                    messages.error(request, " Confirm password and password does not match!")
            except IntegrityError as e:
                messages.error(request, "Email Already Registered!")

        return redirect(f'/administration/all_manager/{company_id}/{company_staff_id}')
    else:
        groups = Group.objects.all()
        return render(request, 'administration/all-manager.html', {'groups': groups,'company_id':company_id, 'company_staff_id':company_staff_id})


@custom_login_required
def All_manager_View(request, company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        manager_obj_id = data.get('manager_id', None)
        manager_obj = Manager.objects.get(pk=manager_obj_id)
        return JsonResponse(manager_obj.to_json())

    # company_id = request.session.get('company')
    if company_id:
        manager = Manager.objects.filter(user__company__id=company_id)
        if manager:
            max_manager_id = Manager.objects.filter(user__company__id=company_id).order_by("-id")[0].id + 1
            return render(request, 'administration/all-manager.html',
                          {'manager': manager, 'max_manager_id': max_manager_id, 'role_choices': role_choices, 'company_id':company_id, 'company_staff_id':company_staff_id})
        else:
            max_manager_id = "NA"
            return render(request, 'administration/all-manager.html',
                          {'manager': manager, 'max_manager_id': max_manager_id, 'role_choices': role_choices, 'company_id':company_id, 'company_staff_id':company_staff_id})


def manager_Edit_View(request,company_id, company_staff_id):
    if company_id:
        if request.method == "GET":
            manager_id = request.GET.get('manager_id')
            manager_obj = Manager.objects.get(pk=manager_id)
            return JsonResponse(manager_obj.to_json())

        elif request.method == "POST":
            manager_models_fields_list = [f.name for f in Manager._meta.get_fields()]
            manager_models_fields_dict = {}
            manager_obj_id = request.POST.get('manager_id')
            manager_obj = Manager.objects.filter(pk=manager_obj_id)

            for key, value in request.POST.items():
                if key in manager_models_fields_list and key != 'manager_id' and key != 'id' and value is not None and len(
                        value) != 0:
                    print(key, value)
                    manager_models_fields_dict.setdefault(key, value)
            manager_obj.update(**manager_models_fields_dict)
            emp_id = request.POST.get('manager_id')

            if 'manager_image' in request.FILES:
                manager_obj = manager_obj.first()
                manager_obj.manager_image = request.FILES['manager_image']
                manager_obj.save()

            print('manager id is-')
            print(emp_id)
            return redirect(f'/administration/all_manager/{company_id}/{company_staff_id}')


@login_required
def All_manager_List_View(request):
    manager = Manager.objects.filter(manager_status="Active")
    return render(request, 'administration/all-manager-list.html', {'manager': manager})



def Remove_manager_List(request, id,company_id, company_staff_id):
    if company_id:
        manager = Manager.objects.get(id=id)
        CompanyStaff.objects.get(id=manager.user.id).delete()
        manager.delete()
        messages.success(request, "deleted successfully")
    return HttpResponseRedirect('/administration/all_manager_list')



def Remove_manager(request, id,company_id,company_staff_id):
    manager_list = Manager.objects.filter(id=id)
    if manager_list.count() > 0:
        managers = manager_list.first()
        try:
            CompanyStaff.objects.get(id=managers.user.id).delete()

            managers.delete()
            messages.success(request, "deleted successfully")
            return redirect(f'/administration/all_manager/{company_id}/{company_staff_id}')
        except:
            return redirect(f'/administration/all_manager/{company_id}/{company_staff_id}')
    print('hii22')
    return redirect(f'/administration/all_manager/{company_id}/{company_staff_id}')


#
# def Remove_manager(request, id,company_id, company_staff_id):
#     if company_id:
#         manager = Manager.objects.get(id=id)
#         CompanyStaff.objects.get(id=manager.company_staff_id).delete()
#         manager.delete()
#         messages.success(request, "deleted successfully")
#         return HttpResponseRedirect('/administration/all_manager',{'company_id':company_id, 'company_staff_id':company_staff_id})


@login_required
def Update_manager_View(request, id):
    update_info = Manager.objects.get(id=id)
    return render(request, 'administration/manager_profile.html', {'update_info': update_info})



@custom_login_required
def IndexView(request, company_id, company_staff_id):
    # company_id = request.session.get('company')
    if company_id:
        projects_count = Task.objects.filter(company_id=company_id).count()
        print('projects_count: ',projects_count)
        clients_count = Client.objects.filter(company_id=company_id).count()
        employee_count = Employee.objects.filter(user__company__id=company_id).count()
        lead_count = Lead.objects.all().count()
        context = {
            'projects_count': projects_count,
            'clients_count': clients_count,
            'employee_count': employee_count,
            'lead_count': lead_count,
            'company_id': company_id,
            'company_staff_id': company_staff_id

        }
    else:
        context = {
            'projects_count': 0,
            'clients_count': 0,
            'employee_count': 0,
            'lead_count': 0,
            'company_staff_id': company_staff_id
        }

    return render(request, "administration/index.html", context)


# --------------------------------------------client------------------------------------------------------------------------
def All_client_View(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        client_obj_id = data.get('id', None)
        client_obj = Client.objects.get(pk=client_obj_id)
        return JsonResponse(client_obj.to_json())

    # Old Code
    if company_id:

        client_list = Client.objects.filter(company_id=company_id)
        context = {
            'client_list': client_list,
            'company_id': company_id,
            'company_staff_id': company_staff_id

        }
        return render(request, 'administration/clients-list.html',context)


def EditClient(request,company_id, company_staff_id):
    if company_id:
        if request.method == "GET":
            id = request.GET.get('id')
            client_obj = Client.objects.get(pk=id)
            return JsonResponse(client_obj.to_json())

        elif request.method == "POST":
            client_models_fields_list = [f.name for f in Client._meta.get_fields()]
            client_models_fields_dict = {}
            client_obj_id = request.POST.get('id')
            client_obj = Client.objects.filter(pk=client_obj_id)

            for key, value in request.POST.items():
                if key in client_models_fields_list and key != 'id' and key != 'id' and value is not None and len(
                        value) != 0:
                    print(key, value)
                    client_models_fields_dict.setdefault(key, value)
            client_obj.update(**client_models_fields_dict)
            emp_id = request.POST.get('id')

            print('client id is-')
            print(emp_id)
            return redirect(f'/administration/client_list/{company_id}/{company_staff_id}')


def CreateClientsView(request,company_id, company_staff_id):
    if company_id:
        try:
            if request.method == 'POST':
                client_first_name = request.POST['client_first_name']
                client_last_name = request.POST['client_last_name']
                client_username = request.POST['client_username']
                client_email = request.POST['client_email']
                client_id = request.POST['client_id']
                client_address = request.POST['client_address']
                client_phone = request.POST['client_phone']
                technology = request.POST['technology']
                description = request.POST['description']
                client_obj = Client(client_first_name=client_first_name,client_last_name=client_last_name,client_address=client_address,client_phone=client_phone,description=description,
                                      client_username=client_username, client_email=client_email,technology=technology,client_id=client_id,company_id=company_id)
                client_obj.save()
                return redirect(f'/administration/client_list/{company_id}/{company_staff_id}')

        except Exception as e:
            print(e)
        return render(request, 'administration/clients.html',{'company_id':company_id, 'company_staff_id':company_staff_id})


# class CreateClientsView(generic.CreateView):
#     model = Client
#     tamplate_name = "administration/clients.html"
#     fields = ('client_first_name', 'client_last_name', 'client_username', 'client_email', 'client_id', 'client_address',
#               'client_phone', 'technology', 'description')
#
#     def get_context_data(self, company_id, company_staff_id, **kwargs):
#         context = super(CreateClientsView, self).get_context_data(**kwargs)
#         return context


class CreateClientsListView(generic.ListView):
    model = Client
    template_name = "administration/clients-list.html"
    context_object_name = "client_list"
    success_url = ('/administration/clients_grid')


class CreateClientsGridView(generic.ListView):
    model = Client
    template_name = "administration/clients-list.html"
    context_object_name = "client_list"
    success_url = ('/administration/clients_grid')


class ClientRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            client = Client.objects.get(id=id)
            client.delete()
            messages.success(request, 'deleted successfuully')
            return redirect(f'/administration/client_list/{company_id}/{company_staff_id}')


class ClientRemoveGrid(View):
    def get(self, request, id):
        client = Client.objects.get(id=id)
        client.delete()
        messages.success(request, 'deleted successfully')
        return HttpResponseRedirect('/administration/clients_grid')


class ClientManageGrid(UpdateView):
    model = Client
    fields = ['client_first_name', 'client_last_name', 'client_username', 'client_email', 'client_id', 'client_address',
              'client_phone', 'client_status']
    context_object_name = "client_update"
    template_name = "administration/client_grid_manage.html"
    success_url = ("/administration/clients_grid/")


class ClientManageList(UpdateView):
    model = Client
    fields = ['client_first_name', 'client_last_name', 'client_username', 'client_email', 'client_id', 'client_address',
              'client_phone', 'client_status']
    context_object_name = "client_list_update"
    template_name = "administration/client_list_manage.html"
    success_url = ("/administration/clients_list/")


# -----------------------------------/client----------------------------------------------------------------

# -------------------------------------Lead----------------------------------------------------------------

def CreateLeadView(request,company_id, company_staff_id):
    if company_id:
        try:
            if request.method == 'POST':
                lead_name = request.POST['lead_name']
                lead_email = request.POST['lead_email']
                lead_phone = request.POST['lead_phone']
                lead_project = request.POST['lead_project']
                lead_assign_staff = request.POST['lead_assign_staff']
                lead_created = request.POST['lead_created']
                lead_source = request.POST['lead_source']

                lead_obj = Lead(lead_name=lead_name,lead_email=lead_email,lead_phone=lead_phone,lead_project=lead_project,
                                      lead_assign_staff=lead_assign_staff, lead_created=lead_created,lead_source=lead_source,company_id=company_id)
                lead_obj.save()
                return redirect(f'/administration/leads_list/{company_id}/{company_staff_id}')

        except Exception as e:
            print(e)
        # return redirect(f'/administration/leads_list/{company_id}/{company_staff_id}')
        return render(request, 'administration/leads.html',{'company_id':company_id, 'company_staff_id':company_staff_id})


# class CreateLeadView(generic.CreateView):
#     model = Lead
#     fields = (
#     'lead_name', 'lead_email', 'lead_phone', 'lead_project', 'lead_assign_staff', 'lead_created', 'lead_source')
#     template_name = "administration/leads.html"
#     success_url = ('/administration/leads_list')


@login_required
def lead_Edit_View(request,company_id, company_staff_id):
    if company_id:
        if request.method == "GET":
            id = request.GET.get('id')
            lead_obj = Lead.objects.get(pk=id)
            return JsonResponse(lead_obj.to_json())

        elif request.method == "POST":
            lead_models_fields_list = [f.name for f in Lead._meta.get_fields()]
            lead_models_fields_dict = {}
            lead_obj_id = request.POST.get('id')
            lead_obj = Lead.objects.filter(pk=lead_obj_id)

            for key, value in request.POST.items():
                if key in lead_models_fields_list and key != 'id' and key != 'id' and value is not None and len(
                        value) != 0:
                    print(key, value)
                    lead_models_fields_dict.setdefault(key, value)
            lead_obj.update(**lead_models_fields_dict)
            emp_id = request.POST.get('id')

            print('lead id is-')
            print(emp_id)
            return redirect(f'/administration/leads_list/{company_id}/{company_staff_id}')



def All_lead_View(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        lead_obj_id = data.get('id', None)
        lead_obj = Lead.objects.get(pk=lead_obj_id)
        return JsonResponse(lead_obj.to_json())

    # Old Code
    if company_id:
        lead_list = Lead.objects.filter(company_id=company_id)
        context = {
            'lead_list': lead_list,
            'company_id': company_id,
            'company_staff_id': company_staff_id

        }
        return render(request, 'administration/leads.html',context)


class LeadsRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            lead = Lead.objects.get(id=id)
            lead.delete()
            messages.success(request, f"{lead} deleted successfully")
        return redirect(f'/administration/leads_list/{company_id}/{company_staff_id}')


class LeadManage(UpdateView):
    model = Lead
    fields = ['lead_name', 'lead_email', 'lead_phone', 'lead_project', 'lead_assign_staff', 'lead_created',
              'lead_source']
    context_object_name = "lead_update"
    template_name = "administration/lead_manage.html"
    success_url = ("/administration/leads_list/")


def ChangePassword(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            current = request.POST["cpwd"]
            new_pas = request.POST["npwd"]

            user = User.objects.get(id=request.user.id)
            un = user.email
            check = user.check_password(current)
            if check == True:
                user.set_password(new_pas)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed Successfully')
                user = User.objects.get(email=un)
                login(request, user)
            else:
                messages.error(request, 'Incorrect Current Password')

        return render(request, "administration/setting_change_password.html")


def All_entry(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        entry_obj_id = data.get('id', None)
        entry_obj = Entries.objects.get(pk=entry_obj_id)
        return JsonResponse(entry_obj.to_json())

    if company_id:
        entry_list = Entries.objects.filter(user__user__company_id=company_id)
        context = {
            'entry_list':  entry_list,
            'company_id': company_id,
            'company_staff_id': company_staff_id

        }
        return render(request, 'administration/view-timesheet.html', context)


class EntryDetailView(DetailView):
    """
    View to show detail info about an Entry
    """
    model = Entries
    template_name = "administration/detail.html"


class EntryRemove(View):
    def get(self, request, id):
        entry_list = Entries.objects.get(id=id)
        entry_list.delete()
        messages.success(request, f"{entry_list} deleted successfully")
        return HttpResponseRedirect('/administration/index')


@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = User.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)


def TaskCreateView(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            title = request.POST.get("title")
            description = request.POST.get("description")
            assign_id = request.POST.get("manager_id")
            assigned_to = Manager.objects.get(id =assign_id)
            # company_staff = CompanyStaff.objects.get(id=company_staff_id)
            # user = company_staff
            # emp = Employee.objects.get(user = user)

            Task.objects.create(title=title,description=description,assigned_to=assigned_to)
            return redirect(f'/administration/projectlist/{company_id}/{company_staff_id}')

        else:
            return render(request,"administration/add-project.html",{'assigned':Manager.objects.filter(user__company__id=company_id),'company_id':company_id, 'company_staff_id':company_staff_id})


# class TaskCreateView(CreateView, LoginRequiredMixin):
#     model = Task
#     fields = ['title', 'description', 'assigned_to']
#
#     def form_valid(self, form):
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)


class TaskDetailView(DetailView, LoginRequiredMixin):
    model = Task
    template_name = "administration/task_detail.html"


class TaskDeleteView(DeleteView, LoginRequiredMixin, UserPassesTestMixin):
    model = Task
    success_url = '/administration/index/'

    def test_func(self):
        task = self.get_object()
        return self.request.user == task.created_by

def attendance(request,company_id, company_staff_id):
    if company_id:
        attendance = Attendance.objects.filter(employee__user__company__id=company_id)
        context = {
            'attendance': attendance,
            'company_id': company_id,
            'company_staff_id':company_staff_id,

        }
    return render(request, 'administration/employee-attendance-list.html',context)

def Project_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        project_obj_id = data.get('id', None)
        project_obj = Task.objects.get(pk=project_obj_id)
        return JsonResponse(project_obj.to_json())

    if company_id:
        project =Task.objects.filter(assigned_to__user__company__id=company_id)
        context = {
            'project': project,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
    return render(request, 'administration/list-project.html', context)


class ProjectRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            project = Task.objects.get(id=id)
            project.delete()
            return redirect(f'/administration/projectlist/{company_id}/{company_staff_id}')


def leaves_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        leave_obj_id = data.get('id', None)
        leave_obj = ManagerLeave.objects.get(pk=leave_obj_id)
        return JsonResponse(leave_obj.to_json())

    if company_id:
        leaves = ManagerLeave.objects.all_pending_leaves().filter(user__user__company_id=company_id)
        return render(request, 'administration/pending-leaves.html',
                      {'leave_list': leaves, 'title': 'leaves list - pending','company_id':company_id, 'company_staff_id':company_staff_id})


def leaves_approved_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        leave_obj_id = data.get('id', None)
        leave_obj = ManagerLeave.objects.get(pk=leave_obj_id)
        return JsonResponse(leave_obj.to_json())

    if company_id:
        leaves = ManagerLeave.objects.all_approved_leaves().filter(user__user__company_id=company_id)  # approved leaves -> calling model manager method
        return render(request, 'administration/approved-leaves.html',
                      {'leave_list': leaves, 'title': 'approved leave list','company_id':company_id, 'company_staff_id':company_staff_id})


def leaves_view(request, id):
    if not (request.user.is_authenticated):
        return redirect('/')

    leave = get_object_or_404(ManagerLeave, id=id)
    print(leave.user)

    return render(request, 'administration/leave_detail_view.html', {'leave': leave,
                                                                     'title': '{0}-{1} leave'.format(
                                                                         leave.user.username,
                                                                         leave.status)})


def approve_leave(request,company_id, company_staff_id, id):
    leave = get_object_or_404(ManagerLeave, id=id)
    # user = leave.user
    # employee = Employee.objects.filter(user=user)
    leave.approve_leave

    messages.error(request, 'Leave successfully approved',
                   extra_tags='alert alert-success alert-dismissible show')
    return redirect(f'/administration/leaves/approved/all/{company_id}/{company_staff_id}')


def cancel_leaves_list(request):
    if not (request.user.is_superuser and request.user.is_authenticated):
        return redirect('/')
    leaves = ManagerLeave.objects.all_cancel_leaves()
    return render(request, 'administration/cancelled-leaves.html',
                  {'leave_list_cancel': leaves, 'title': 'Cancel leave list'})


def unapprove_leave(request, id):
    if not (request.user.is_authenticated and request.user.is_superuser):
        return redirect('/')
    leave = get_object_or_404(ManagerLeave, id=id)
    leave.unapprove_leave
    return redirect('leaveslist')  # redirect to unapproved list


def cancel_leave(request, id):
    if not (request.user.is_superuser and request.user.is_authenticated):
        return redirect('/')
    leave = get_object_or_404(ManagerLeave, id=id)
    leave.leaves_cancel

    messages.success(request, 'Leave is canceled', extra_tags='alert alert-success alert-dismissible show')
    return redirect('canceleaveslist')  # work on redirecting to instance leave - detail view


# Current section -> here
def uncancel_leave(request, id):
    if not (request.user.is_superuser and request.user.is_authenticated):
        return redirect('/')
    leave = get_object_or_404(ManagerLeave, id=id)
    leave.status = 'pending'
    leave.is_approved = False
    leave.save()
    messages.success(request, 'Leave is uncanceled,now in pending list',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('canceleaveslist')  # work on redirecting to instance leave - detail view


def leave_rejected_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        leave_obj_id = data.get('id', None)
        leave_obj = ManagerLeave.objects.get(pk=leave_obj_id)
        return JsonResponse(leave_obj.to_json())

    if company_id:
        dataset = dict()
        leave = ManagerLeave.objects.all_rejected_leaves().filter(user__user__company_id=company_id)

        dataset['leave_list_rejected'] = leave
        dataset[ 'company_id'] =  company_id
        dataset['company_staff_id'] = company_staff_id
        return render(request, 'administration/rejected-leaves.html', dataset)


def reject_leave(request,company_id, company_staff_id,id):
    dataset = dict()
    leave = get_object_or_404(ManagerLeave, id=id)
    leave.reject_leave
    messages.success(request, 'Leave is rejected', extra_tags='alert alert-success alert-dismissible show')
    return redirect(f'/administration/leaves/rejected/all/{company_id}/{company_staff_id}')



def unreject_leave(request, id):
    leave = get_object_or_404(ManagerLeave, id=id)
    leave.status = 'pending'
    leave.is_approved = False
    leave.save()
    messages.success(request, 'Leave is now in pending list ', extra_tags='alert alert-success alert-dismissible show')

    return redirect('leavesrejected')


def Balance_list(request,company_id, company_staff_id):
    if company_id:
        balance = ManagerLeave.objects.filter(user__user__company_id=company_id)
        context = {
            'balance': balance,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'administration/leaves-balance-list.html', context)


class BalanceRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            balance = ManagerLeave.objects.get(id=id)
            balance.delete()
            return redirect(f'/administration/balancelist/{company_id}/{company_staff_id}')



def notifications(request,company_id, company_staff_id):
    if company_id:
        notify = notification.objects.filter(company__id=company_id)
        context = {
            'notify': notify ,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'administration/notifications.html', context)


def createnotifications(request,company_id, company_staff_id):
    if company_id:
        try:
            if request.method == 'POST':
                notify = request.POST['notify']
                print(notify)
                notify_obj = notification(notify=notify)
                notify_obj.save()
                return render(request, 'administration/notifications.html', {'msg': 'Notification added successfully'},{'company_id':company_id, 'company_staff_id':company_staff_id})
        except Exception as e:
            print(e)
        return render(request, 'administration/notifications.html',{'company_id':company_id, 'company_staff_id':company_staff_id})


def getnotification(request):
    notify = notification.objects.all()
    notify_obj = [{'notify': i.notify} for i in notify]
    return JsonResponse({'notify': notify_obj})


def getattendance(request):
    attendance = Attendance.objects.all()
    attendance_obj = [{'employee__employee_id': i.employee_id, 'check_in': i.check_in, 'check_out': i.check_out}
                      for i in attendance]
    return JsonResponse({'attendance': attendance_obj})


def attendance(request,company_id, company_staff_id):
    if company_id:
        attendance = Attendance.objects.filter(employee__user__company__id=company_id)
        context = {
            'attendance': attendance,
            'company_id': company_id,
            'company_staff_id':company_staff_id,

        }
    return render(request, 'administration/employee-attendance-list.html',context)


def attendance_Edit_View(request,company_id, company_staff_id):
    if company_id:
        if request.method == "GET":
            id = request.GET.get('id')
            attendance_obj = Attendance.objects.get(pk=id)
            return JsonResponse(attendance_obj.to_json())

        elif request.method == "POST":
            attendance_models_fields_list = [f.name for f in Attendance._meta.get_fields()]
            attendance_models_fields_dict = {}
            attendance_obj_id = request.POST.get('id')
            attendance_obj = Attendance.objects.filter(pk=attendance_obj_id)

            for key, value in request.POST.items():
                if key in attendance_models_fields_list and key != 'id' and key != 'id' and value is not None and len(
                        value) != 0:
                    print(key, value)
                    attendance_models_fields_dict.setdefault(key, value)
            attendance_obj.update(**attendance_models_fields_dict)
            emp_id = request.POST.get('id')

            # print('attendance id is-')
            # print(emp_id)
            return redirect(f'/administration/attendancee/{company_id}/{company_staff_id}')


class AttendanceRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            attendance = Attendance.objects.get(id=id)
            attendance.delete()
            messages.success(request, f"{attendance} deleted successfully")
            return redirect(f'/administration/attendancee/{company_id}/{company_staff_id}')


class AttendanceManage(UpdateView):
    model = Attendance
    fields = ['check_in', 'check_out']
    context_object_name = "attendance_update"
    template_name = "administration/attendance_manage.html"
    success_url = ("/administration/attendancee/")

    def post(self, request, pk):
        data = Attendance.objects.get(id=pk)
        data.check_out = request.POST.get('check_out')
        data.check_in = request.POST.get('check_in')
        data.save()
        print(str(data) + "=" + str(request.POST.get('check_out')))
        return HttpResponseRedirect("/administration/attendancee/")


def Attendancesearch(request,company_id, company_staff_id):
    if 'q' in request.GET:
        q = request.GET['q']
        multiple_q = Q(Q(employee__user__email__icontains=q) | Q(check_in__icontains=q) | Q(check_out__icontains=q))
        attendance = Attendance.objects.filter(multiple_q)
    else:
        attendance = Attendance.objects.filter(employee__user__company__id=company_id)
    context = {
        'attendance': attendance,
        'company_id': company_id,
        'company_staff_id': company_staff_id
    }
    return render(request, 'administration/employee-attendance-list.html', context)



def resign_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        resign_obj_id = data.get('id', None)
        resign_obj = ManagerResign.objects.get(pk=resign_obj_id)
        return JsonResponse(resign_obj.to_json())

    if company_id:
        resign = ManagerResign.objects.all_pending_resign().filter(user__user__company_id=company_id)
        return render(request, 'administration/pending-resignation.html',
                      {'resign_list': resign, 'title': 'resign list - pending','company_id':company_id, 'company_staff_id':company_staff_id})


def resign_approved_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        resign_obj_id = data.get('id', None)
        resign_obj = ManagerResign.objects.get(pk=resign_obj_id)
        return JsonResponse(resign_obj.to_json())

    if company_id:
        resign = ManagerResign.objects.all_approved_resign().filter(user__user__company_id=company_id)  # approved leaves -> calling model manager method
        return render(request, 'administration/approved-resignation.html',
                      {'resign_list': resign, 'title': 'approved resign list','company_id':company_id, 'company_staff_id':company_staff_id})


def resign_view(request, id):
    if not (request.user.is_authenticated):
        return redirect('/')

    resign = get_object_or_404(Resign, id=id)

    # employee = Employee.objects.filter(user=resign.user)[0]
    # print(employee)
    return render(request, 'administration/resign_detail_view.html', {'resign': resign,
                                                                      'title': '{0}-{1} resign'.format(
                                                                          resign.user.username,
                                                                          resign.status)})


def approve_resign(request,company_id, company_staff_id, id):

    resign = get_object_or_404(ManagerResign, id=id)
    # user = resign.user
    resign.approve_resign

    messages.error(request, 'Resignation successfully approved',
                   extra_tags='alert alert-success alert-dismissible show')
    return redirect(f'/administration/resign/approved/all/{company_id}/{company_staff_id}')


def cancel_resign_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        resign_obj_id = data.get('id', None)
        resign_obj = ManagerResign.objects.get(pk=resign_obj_id)
        return JsonResponse(resign_obj.to_json())

    if company_id:
        resign = ManagerResign.objects.all_cancel_resign().filter(user__user__company_id=company_id)
        return render(request, 'administration/cancelled-resignation.html',
                      {'resign_list': resign, 'title': 'Cancel resign list','company_id':company_id, 'company_staff_id':company_staff_id})


def unapprove_resign(request, id):
    if not (request.user.is_authenticated and request.user.is_superuser):
        return redirect('/')
    resign = get_object_or_404(Resign, id=id)
    resign.unapprove_resign
    return redirect('resignlist')  # redirect to unapproved list


def cancel_resign(request,company_id, company_staff_id, id):

    resign = get_object_or_404(ManagerResign, id=id)
    resign.resign_cancel

    messages.success(request, 'Resign is canceled', extra_tags='alert alert-success alert-dismissible show')
    return redirect(f'/administration/resign/cancel/all/{company_id}/{company_staff_id}')


# Current section -> here
def uncancel_resign(request, id):
    if not (request.user.is_superuser and request.user.is_authenticated):
        return redirect('/')
    resign = get_object_or_404(Resign, id=id)
    resign.status = 'pending'
    resign.is_approved = False
    resign.save()
    messages.success(request, 'Leave is uncanceled,now in pending list',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('cancelresignlist')


def resign_rejected_list(request):
    dataset = dict()
    resign = Resign.objects.all_rejected_resign()

    dataset['resign_list_rejected'] = resign
    return render(request, 'administration/rejected_resign_list.html', dataset)


def reject_resign(request, id):
    dataset = dict()
    resign = get_object_or_404(Leave, id=id)
    resign.reject_leave
    messages.success(request, 'Resignation is rejected', extra_tags='alert alert-success alert-dismissible show')
    return redirect('resignrejected')


# return HttpResponse(id)


def unreject_resign(request, id):
    resign = get_object_or_404(Resign, id=id)
    resign.status = 'pending'
    resign.is_approved = False
    resign.save()
    messages.success(request, 'Resignation is now in pending list ',
                     extra_tags='alert alert-success alert-dismissible show')

    return redirect('resignrejected')


def holidays(request,company_id, company_staff_id):
    if company_id:
        try:
            if request.method == 'POST':
                day = request.POST['day']
                print(day)
                date = request.POST['date']
                print(date)
                occassion = request.POST['occassion']
                print(occassion)
                type = request.POST['type']
                print(type)
                status = 1
                holiday_obj = holiday(day=day, date=date,
                                      occassion=occassion, holidaytype=type, status=status,company_id=company_id)
                holiday_obj.save()
                return render(request, 'administration/add-holiday.html', {'msg': 'Data updated'},{'company_id':company_id, 'company_staff_id':company_staff_id})
        except Exception as e:
            print(e)
        return render(request, 'administration/add-holiday.html',{'company_id':company_id, 'company_staff_id':company_staff_id})

#
# def holidays(request,company_id, company_staff_id):
#     if request.method == 'POST':
#         day = request.POST['day']
#         print(day)
#         date = request.POST['date']
#         print(date)
#         occassion = request.POST['occassion']
#         print(occassion)
#         type = request.POST['type']
#         print(type)
#         status = 1
#         if company_id:
#
#             holiday_obj = holiday(day=day, date=date,
#                                   occassion=occassion, holidaytype=type, status=status)
#             holiday_obj.save()
#             return render(request, 'administration/add-holiday.html', {'msg': 'Data updated'},{'company_id':company_id, 'company_staff_id':company_staff_id})
#
#     return render(request, 'administration/add-holiday.html',{'company_id':company_id, 'company_staff_id':company_staff_id})


def fnholidays(request):
    holidays = holiday.objects.all()
    holiday_obj = [{'id': i.id, 'day': i.day, 'date': i.date,
                    'occassion': i.occassion, 'type': i.holidaytype} for i in holidays]
    print(holiday_obj)
    return JsonResponse({'holiday': holiday_obj})


def getdatas(request):
    user = Employee.objects.all()
    user_obj = [{'id': i.id} for i in user]
    holidays = holiday.objects.all().count()
    return JsonResponse({'user': user_obj, 'holiday': holidays})


def holiday_list(request,company_id, company_staff_id):
    if company_id:
        holyday = holiday.objects.filter(company_id=company_id)
        context = {
            'holyday': holyday,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'administration/list-holiday.html', context)


class delholiday(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            holyday = holiday.objects.get(id=id)
            holyday.delete()
            messages.success(request, f"{holyday} deleted successfully")
            return redirect(f'/administration/holidaylist/{company_id}/{company_staff_id}')


class PostListView(ListView):
    def dispatch(self, request, company_id, company_staff_id, *args, **kwargs):
        print('Dispatch function called')
        company_staff = CompanyStaff.objects.filter(pk=company_staff_id)
        if company_staff.exists():
            if company_staff.first().is_authenticated:
                return super().dispatch(request, company_id, company_staff_id, *args, **kwargs)
            else:
                return redirect('/')
        else:
            return redirect('/')

    model = Post
    template_name = 'administration/employee-all-documents.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 2


def All_document_View(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        document_obj_id = data.get('id', None)
        document_obj = Post.objects.get(pk=document_obj_id)
        return JsonResponse(document_obj.to_json())

    # Old Code
    if company_id:
        posts= Post.objects.filter(user__user__company__id=company_id)
        return render(request, 'administration/employee-all-documents.html',{'posts': posts,'company_id':company_id, 'company_staff_id':company_staff_id})


def search(request):
    template = 'administration/employee-all-documents.html'

    query = request.GET.get('q')

    result = Post.objects.filter(
        Q(user__employee_email__icontains=query))
    paginate_by = 2
    context = {'posts': result}
    return render(request, template, context)


class UserPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'administration/employee-all-documents.html'
    context_object_name = 'posts'
    paginate_by = 2

    def get_queryset(self):
        queryset = super(UserPostListView, self).get_queryset()
        queryset = Post.objects.filter(user=self.request.user.employee)
        return queryset

# class PostDetailView(View):
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
#     def get(self,company_id, company_staff_id):
#         posts = Post.objects.filter(company__id=company_id)
#         context = {
#             "posts": posts,
#             'company_id': company_id,
#             'company_staff_id': company_staff_id
#
#         }
#
#         return render(self.request, 'administration/employee_documents.html', context)
#
#
def PostDetailView(request,company_id, company_staff_id,id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        document_obj_id = data.get('id', None)
        document_obj = Post.objects.get(pk=document_obj_id)
        return JsonResponse(document_obj.to_json())

    # Old Code
    if company_id:
        # company_staff = CompanyStaff.objects.get(id=company_staff_id)
        document_list = Post.objects.filter(id=id)
        # document_list = Post.objects.filter(user=company_staff)
        return render(request, 'administration/employee_documents.html',
                      {'document_list': document_list,'company_id':company_id, 'company_staff_id':company_staff_id})

# def PostDetailView(request,company_id, company_staff_id,id):
#
#     if company_id:
#         posts = get_object_or_404(Post, id=id)
#
#         return render(request, 'administration/employee_documents.html', {'posts':posts,'company_id':company_id, 'company_staff_id':company_staff_id})


# class PostDetailView(DetailView):
#     model = Post
#     template_name = 'administration/employee_documents.html'
#
#

class PostDeleteView(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            posts = Post.objects.get(id=id)
            posts.delete()
            messages.success(request, f"{posts} deleted successfully")
            return redirect(f'/administration/all_document_View/{company_id}/{company_staff_id}')

def DepartmentCreateView(request,company_id, company_staff_id):
    if company_id:
        try:
            if request.method == 'POST':
                department_name = request.POST['department_name']
                department_name = Department( department_name= department_name,company_id=company_id)
                department_name.save()
                return redirect(f'/administration/department_lst/{company_id}/{company_staff_id}')

        except Exception as e:
            print(e)
        return render(request, 'administration/department.html',{'company_id':company_id, 'company_staff_id':company_staff_id})


# class DepartmentCreateView(generic.CreateView):
#     model = Department
#     fields = ('department_name',)
#     template_name = "administration/department.html"
#     success_url = ('/administration/department_lst')
#
def DepartmentList(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        client_obj_id = data.get('id', None)
        client_obj = Client.objects.get(pk=client_obj_id)
        return JsonResponse(client_obj.to_json())

    # Old Code
    if company_id:
        department_list = Department.objects.filter(company_id=company_id)
        context = {
            'department_list': department_list,
            'company_id': company_id,
            'company_staff_id': company_staff_id

        }
        return render(request, 'administration/department.html',context)


# class DepartmentList(generic.ListView):
#     model = Department
#     template_name = "administration/department.html"
#     context_object_name = "department_list"
#     success_url = ('/administration/department_lst')


def department_Edit_View(request,company_id, company_staff_id):
    if company_id:
        if request.method == "GET":
            id = request.GET.get('id')
            department_obj = Department.objects.get(pk=id)
            return JsonResponse(department_obj.to_json())

        elif request.method == "POST":
            department_models_fields_list = [f.name for f in Department._meta.get_fields()]
            department_models_fields_dict = {}
            department_obj_id = request.POST.get('id')
            department_obj = Department.objects.filter(pk=department_obj_id)

            for key, value in request.POST.items():
                if key in department_models_fields_list and key != 'id' and key != 'id' and value is not None and len(
                        value) != 0:
                    print(key, value)
                    department_models_fields_dict.setdefault(key, value)
            department_obj.update(**department_models_fields_dict)
            emp_id = request.POST.get('id')

            print('department id is-')
            print(emp_id)
            return redirect(f'/administration/department_lst/{company_id}/{company_staff_id}')


class DepartmentRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            department = Department.objects.get(id=id)
            department.delete()
            messages.success(request, f"{department} deleted successfully")
            return redirect(f'/administration/department_lst/{company_id}/{company_staff_id}')


class ManageDepartment(UpdateView):
    model = Department
    fields = ['department_name']
    context_object_name = "department_update"
    template_name = "administration/department_manage.html"
    success_url = ("/administration/department_list/")


def regularization_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = Regularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    if company_id:
        regularization = Regularization.objects.all_pending_regularization().filter(user__user__company__id=company_id)
        return render(request, 'administration/employee-pending-regularization.html',
                      {'regularization_list': regularization, 'title': 'regularization list - pending','company_id':company_id, 'company_staff_id':company_staff_id})


def regularization_approved_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = Regularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    regularization = Regularization.objects.all_approved_regularization().filter(user__user__company__id=company_id)  # approved leaves -> calling model manager method
    return render(request, 'administration/employee-approved-regularization.html',
                  {'regularization_list': regularization, 'title': 'approved regularization list','company_id':company_id, 'company_staff_id':company_staff_id})


def approve_regularization(request,company_id, company_staff_id, id):
    if company_id:
        regularization = get_object_or_404(Regularization, id=id)
        regularization.approve_regularization

        messages.success(request, 'regularization is approved', extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/administration/regularization/approved/all/{company_id}/{company_staff_id}')


def cancel_regularization_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = Regularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    regularization = Regularization.objects.all_cancel_regularization().filter(user__user__company__id=company_id)
    return render(request, 'administration/employee-cancelled-regularization.html',
                  {'regularization_list_cancel': regularization, 'title': 'Cancel regularization list','company_id':company_id, 'company_staff_id':company_staff_id})


def unapprove_regularization(request, id):
    if not (request.user.is_authenticated and request.user.is_superuser):
        return redirect('/')
    regularization = get_object_or_404(Regularization, id=id)
    regularization.unapprove_regularization
    return redirect('regularizationlist')  # redirect to unapproved list


def cancel_regularization(request,company_id, company_staff_id, id):
    if company_id:
        regularization = get_object_or_404(Regularization, id=id)
        regularization.regularization_cancel

        messages.success(request, 'regularization is canceled', extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/administration/regularization/cancel/all/{company_id}/{company_staff_id}')



# Current section -> here
def uncancel_regularization(request, id):
    if not (request.user.is_superuser and request.user.is_authenticated):
        return redirect('/')
    regularization = get_object_or_404(Regularization, id=id)
    regularization.status = 'pending'
    regularization.is_approved = False
    regularization.save()
    messages.success(request, 'Leave is uncanceled,now in pending list',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('cancelregularizationlist')


def regularization_rejected_list(request):
    dataset = dict()
    regularization = Regularization.objects.all_rejected_regularization()

    dataset['regularization_list_rejected'] = regularization
    return render(request, 'administration/rejected_regularization_list.html', dataset)


def reject_regularization(request, id):
    dataset = dict()
    regularization = get_object_or_404(Leave, id=id)
    regularization.reject_leave
    messages.success(request, 'regularizationation is rejected',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('regularizationrejected')



def unreject_regularization(request, id):
    regularization = get_object_or_404(Regularization, id=id)
    regularization.status = 'pending'
    regularization.is_approved = False
    regularization.save()
    messages.success(request, 'regularizationation is now in pending list ',
                     extra_tags='alert alert-success alert-dismissible show')

    return redirect('regularizationrejected')


def mregularization_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = MRegularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    if company_id:
        regularization = MRegularization.objects.all_pending_regularization().filter(user__user__company__id=company_id)
        return render(request, 'administration/manager-pending-regularization.html',
                      {'regularization_list': regularization, 'title': 'regularization list - pending','company_id':company_id, 'company_staff_id':company_staff_id})


def mregularization_approved_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = MRegularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    if company_id:
        regularization = MRegularization.objects.all_approved_regularization().filter(user__user__company__id=company_id) # approved leaves -> calling model manager method
        return render(request, 'administration/manager-approved-regularization.html',
                      {'regularization_list': regularization, 'title': 'approved regularization list','company_id':company_id, 'company_staff_id':company_staff_id})


def mregularization_view(request, id):
    if not (request.user.is_authenticated):
        return redirect('/')

    regularization = get_object_or_404(MRegularization, id=id)

    return render(request, 'administration/mregularization_detail_view.html', {'regularization': regularization,
                                                                               'title': '{0}-{1} regularization'.format(
                                                                                   regularization.user.manager_email,
                                                                                   regularization.status)})


def mapprove_regularization(request, id):
    regularization = get_object_or_404(MRegularization, id=id)

    regularization.approve_regularization

    messages.error(request, 'regularizationation successfully approved',
                   extra_tags='alert alert-success alert-dismissible show')
    return redirect('mapprovedregularizationlist')


def mcancel_regularization_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = MRegularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    if company_id:
        regularization = MRegularization.objects.all_cancel_regularization().filter(user__user__company__id=company_id)
        return render(request, 'administration/manager-cancelled-regularization.html',
                      {'regularization_list': regularization, 'title': 'Cancel regularization list','company_id':company_id, 'company_staff_id':company_staff_id})


def munapprove_regularization(request, id):
    if not (request.user.is_authenticated and request.user.is_superuser):
        return redirect('/')
    regularization = get_object_or_404(MRegularization, id=id)
    regularization.unapprove_regularization
    return redirect('mregularizationlist')  # redirect to unapproved list


def mcancel_regularization(request, id):
    if not (request.user.is_superuser and request.user.is_authenticated):
        return redirect('/')
    regularization = get_object_or_404(MRegularization, id=id)
    regularization.regularization_cancel

    messages.success(request, 'regularization is canceled', extra_tags='alert alert-success alert-dismissible show')
    return redirect('mcancelregularizationlist')  # work on redirecting to instance leave - detail view


# Current section -> here
def muncancel_regularization(request, id):
    if not (request.user.is_superuser and request.user.is_authenticated):
        return redirect('/')
    regularization = get_object_or_404(MRegularization, id=id)
    regularization.status = 'pending'
    regularization.is_approved = False
    regularization.save()
    messages.success(request, 'Regularization is uncanceled,now in pending list',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('mcancelregularizationlist')


def mregularization_rejected_list(request):
    dataset = dict()
    regularization = MRegularization.objects.all_rejected_regularization()

    dataset['regularization_list_rejected'] = regularization
    return render(request, 'administration/mrejected_regularization_list.html', dataset)


def mreject_regularization(request, id):
    dataset = dict()
    regularization = get_object_or_404(Leave, id=id)
    regularization.reject_leave
    messages.success(request, 'regularizationation is rejected',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('mregularizationrejected')



def munreject_regularization(request, id):
    regularization = get_object_or_404(MRegularization, id=id)
    regularization.status = 'pending'
    regularization.is_approved = False
    regularization.save()
    messages.success(request, 'regularizationation is now in pending list ',
                     extra_tags='alert alert-success alert-dismissible show')

    return redirect('mregularizationrejected')


def mattendance(request,company_id, company_staff_id):
    if company_id:
        attendance = ManagerAttendance.objects.filter(manager__user__company__id=company_id)
        context = {
            'attendance': attendance,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'administration/manager-attendance-list.html', context)


def Mattendance_Edit_View(request,company_id, company_staff_id):
    if company_id:
        if request.method == "GET":
            id = request.GET.get('id')
            attendance_obj = ManagerAttendance.objects.get(pk=id)
            return JsonResponse(attendance_obj.to_json())

        elif request.method == "POST":
            attendance_models_fields_list = [f.name for f in ManagerAttendance._meta.get_fields()]
            attendance_models_fields_dict = {}
            attendance_obj_id = request.POST.get('id')
            attendance_obj = ManagerAttendance.objects.filter(pk=attendance_obj_id)

            for key, value in request.POST.items():
                if key in attendance_models_fields_list and key != 'id' and key != 'id' and value is not None and len(
                        value) != 0:
                    print(key, value)
                    attendance_models_fields_dict.setdefault(key, value)
            attendance_obj.update(**attendance_models_fields_dict)
            emp_id = request.POST.get('id')

            print('attendance id is-')
            print(emp_id)
            return redirect(f'/administration/mattendancee/{company_id}/{company_staff_id}')

class mAttendanceRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            attendance = ManagerAttendance.objects.get(id=id)
            attendance.delete()
            messages.success(request, f"{attendance} deleted successfully")
            return redirect(f'/administration/mattendancee/{company_id}/{company_staff_id}')


class mAttendanceManage(UpdateView):
    model = ManagerAttendance
    fields = ['check_in', 'check_out']
    context_object_name = "attendance_update"
    template_name = "administration/manager-attendance-list.html"
    success_url = ("/administration/mattendancee/")

    def post(self, request, pk):
        data = ManagerAttendance.objects.get(id=pk)
        data.check_out = request.POST.get('check_out')
        data.check_in = request.POST.get('check_in')
        data.save()
        print(str(data) + "=" + str(request.POST.get('check_out')))
        return HttpResponseRedirect("/administration/mattendancee/")



def mAttendancesearch(request,company_id, company_staff_id):
    if 'q' in request.GET:
        q = request.GET['q']
        multiple_q = Q(Q(manager__user__email__icontains=q) | Q(check_in__icontains=q) | Q(check_out__icontains=q))
        attendance = ManagerAttendance.objects.filter(multiple_q)
    else:
        attendance = ManagerAttendance.objects.filter(manager__user__company__id=company_id)
    context = {
        'attendance': attendance,
        'company_id': company_id,
        'company_staff_id': company_staff_id
    }
    return render(request, 'administration/manager-attendance-list.html', context)



def assignCreateView(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            employee_id = request.POST.get("employee_id")
            employee_to = Employee.objects.get(id=employee_id)
            description = request.POST.get("description")
            assign_id = request.POST.get("manager_id")
            assigned_to = Manager.objects.get(id =assign_id)
            # company_staff = CompanyStaff.objects.get(id=company_staff_id)
            # user = company_staff
            # emp = Employee.objects.get(user = user)

            Asign.objects.create(employee=employee_to,description=description,assigned_to=assigned_to)
            return redirect(f'/administration/assignlist/{company_id}/{company_staff_id}')

        else:
            return render(request,"administration/assign-employee.html",{'assigned':Manager.objects.filter(user__company__id=company_id),'assignedto':Employee.objects.filter(user__company__id=company_id),'company_id':company_id, 'company_staff_id':company_staff_id})


# class assignCreateView(CreateView, LoginRequiredMixin):
#     model = Asign
#     fields = ['employee', 'description', 'assigned_to']
#
#     def form_valid(self, form):
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)


class assignDetailView(DetailView, LoginRequiredMixin):
    model = Asign
    template_name = "administration/assign-employee.html"


class aasignDeleteView(DeleteView, LoginRequiredMixin, UserPassesTestMixin):
    model = Asign
    success_url = '/administration/index/'

    def test_func(self):
        assign = self.get_object()
        return self.request.user == assign.created_by


def Assign_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        assign_obj_id = data.get('id', None)
        assign_obj = Asign.objects.get(pk=assign_obj_id)
        return JsonResponse(assign_obj.to_json())

    if company_id:
        assign = Asign.objects.filter(employee__user__company__id=company_id)
        context = {
            'assign': assign,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'administration/employee-list.html', context)


class AssignRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        assign = Asign.objects.get(id=id)
        assign.delete()
        return redirect(f'/administration/assignlist/{company_id}/{company_staff_id}')


def All_document_Views(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        document_obj_id = data.get('id', None)
        document_obj = ManagerPost.objects.get(pk=document_obj_id)
        return JsonResponse(document_obj.to_json())

    # Old Code
    if company_id:
        document_list = ManagerPost.objects.filter(user__user__company__id=company_id)
        return render(request, 'administration/manager-all-documents.html',
                      {'document_list': document_list,'company_id':company_id, 'company_staff_id':company_staff_id})



class ManagerPostListView(ListView):
    def dispatch(self, request, company_id, company_staff_id, *args, **kwargs):
        print('Dispatch function called')
        company_staff = CompanyStaff.objects.filter(pk=company_staff_id)
        if company_staff.exists():
            if company_staff.first().is_authenticated:
                return super().dispatch(request, company_id, company_staff_id, *args, **kwargs)
            else:
                return redirect('/')
        else:
            return redirect('/')

    model = ManagerPost
    template_name = 'administration/manager-all-documents.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 2




class MPostListView(LoginRequiredMixin, ListView):
    model = ManagerPost
    template_name = 'administration/manager-all-documents.html'
    context_object_name = 'posts'
    paginate_by = 2

    def get_queryset(self):
        queryset = super(MPostListView, self).get_queryset()
        queryset = ManagerPost.objects.filter(user=self.request.user.manager)
        return queryset

def MPostDetailView(request,company_id, company_staff_id,id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        document_obj_id = data.get('id', None)
        document_obj = Post.objects.get(pk=document_obj_id)
        return JsonResponse(document_obj.to_json())

    # Old Code
    if company_id:
        # company_staff = CompanyStaff.objects.get(id=company_staff_id)
        document_list = ManagerPost.objects.filter(id=id)
        # document_list = Post.objects.filter(user=company_staff)
        return render(request, 'administration/manager_documents.html',
                      {'document_list': document_list,'company_id':company_id, 'company_staff_id':company_staff_id})


# class MPostDetailView(DetailView):
#     model = ManagerPost
#     template_name = 'administration/manager_documents.html'


class MPostDeleteView(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            posts = ManagerPost.objects.get(id=id)
            posts.delete()
            messages.success(request, f"{posts} deleted successfully")
            return redirect(f'/administration/manager_document_View/{company_id}/{company_staff_id}')


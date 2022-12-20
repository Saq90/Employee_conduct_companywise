import json
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect, render, get_object_or_404
from django.views import generic
from django.views.generic import View
from django.contrib.auth.hashers import  make_password
from administration.models import Task, notification, holiday, MTask
from leave.forms import LeaveCreationForm
from leave.models import Leave, BalanceLeaves
from manager_leave.models import BalanceLeave
from managers.models import Manager
from payroll.models import Salary
from regularization.forms import RegularizationCreationForm
from regularization.models import Regularization
from resign.forms import ResignCreationForm
from resign.models import Resign
from account.models import CompanyStaff
from .helpers.enum import attendance_type
from .helpers.helper import getgriddatapaginated, strfdelta, ajax_response
from .models import Employee, Attendance, Entries
from django.db import IntegrityError
from django.contrib import messages
from django.views.generic import TemplateView, CreateView, ListView
from .models import Employee, Department, Designation
from .forms import DepartmentForm, DesignationForm, EntryCreationForm
from django.urls import reverse_lazy, reverse
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Post
from django.contrib.staticfiles.views import serve
from django.db.models import Q
from django.contrib.auth import get_user_model
User = get_user_model()


def employee_profile_view(request,company_id, company_staff_id):

    company_staff = CompanyStaff.objects.get(id=company_staff_id)
    profile = Employee.objects.filter(user=company_staff).first()
    if company_id:
        if request.method == "POST":
            data = dict(request.POST.copy())
            for field, value in data.items():
                if field != 'csrfmiddlewaretoken' and field != 'employee_image':
                    setattr(profile, field, value[0])

            if 'employee_image' in request.FILES:
                profile.employee_image = request.FILES['employee_image']

            profile.save()
        return render(request, 'employee/my-profile.html', {'profile': profile,'company_id': company_id, 'company_staff_id': company_staff_id})
    return render(request, 'employee/my-profile.html', {'profile': profile},{'company_id':company_id, 'company_staff_id':company_staff_id})


class EmployeeUpdateView(UpdateView):
    model = Employee
    template_name = 'employee/my-profile.html'
    fields = '__all__'
    context_object_name = 'employee_update'


def EmployeeDashboardView(request, company_id, company_staff_id):
    ctx = {}
    today = datetime.now().date()
    tomorrow = today + timedelta(1)

    company_staff = CompanyStaff.objects.get(id=company_staff_id)
    att = Attendance.objects.filter(Q(check_in__gt=today)
                                    & Q(check_in__lt=tomorrow)
                                    & Q(employee=company_staff.employee)).first()
    ctx['attendance'] = att
    ctx['company_id'] = company_id
    ctx['company_staff_id'] = company_staff_id
    if att:
        ctx['hours_num'] = strfdelta((att.check_out - att.check_in),
                                     "{hours}:{minutes}:{seconds}") if att.check_out else ''
        ctx['is_check_in'] = attendance_type.check_out.value
        ctx['is_complete_attendance'] = True if att.check_in and att.check_out else False
    else:
        ctx['is_check_in'] = attendance_type.check_in.value
    return render(request, "employee/index.html", ctx)


def leave_creation(request,company_id, company_staff_id):
    if company_id:
        if request.method == 'POST':
            form = LeaveCreationForm(data=request.POST)
            if form.is_valid():
                instance = form.save(commit=False)
                company_staff = CompanyStaff.objects.get(id=company_staff_id)
                user = company_staff
                instance.user = company_staff
                instance.save()
                messages.success(request, 'Leave Request Sent,wait for response',
                                 extra_tags='alert alert-success alert-dismissible show')
                return redirect(f'/employee/leaves/view/table/{company_id}/{company_staff_id}')
            messages.error(request, 'failed to Request a Leave,please check entry dates',
                           extra_tags='alert alert-warning alert-dismissible show')
        return redirect(f'/employee/leave/{company_id}/{company_staff_id}')

    dataset = dict()
    form = LeaveCreationForm()
    dataset['form'] = form
    dataset['title'] = 'Apply for Leave'
    dataset['company_id'] = company_id
    dataset['company_staff_id'] = company_staff_id
    return render(request, 'employee/apply-leaves.html', dataset)


def view_my_leave_table(request,company_id, company_staff_id):

    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        user =  company_staff.employee
        leaves = Leave.objects.filter(user=user)
        print(leaves)
        dataset = dict()
        dataset['leave_list'] = leaves
        # dataset['employee'] = employee
        dataset['title'] = 'Leaves List'
        dataset['company_id'] = company_id
        dataset['company_staff_id'] = company_staff_id
    else:
        return redirect('accounts:login')
    return render(request, 'employee/leave-status.html', dataset)


class LeaveRemove(View):
    def get(self, request, id):
        leave = Leave.objects.get(id=id)
        leave.delete()
        return HttpResponseRedirect('/employee/employee_dashboard/')


def attendance(request,company_id, company_staff_id):
    ctx = {}
    today = datetime.now().date()
    tomorrow = today + timedelta(1)

    company_staff = CompanyStaff.objects.get(id=company_staff_id)
    att = Attendance.objects.filter(Q(check_in__gt=today)
                                    & Q(check_in__lt=tomorrow)
                                    & Q(employee=company_staff.employee)).first()
    ctx['attendance'] = att
    ctx['company_id'] = company_id
    ctx['company_staff_id'] = company_staff_id
    if att:
        ctx['hours_num'] = strfdelta((att.check_out - att.check_in),
                                     "{hours}:{minutes}:{seconds}") if att.check_out else ''
        ctx['is_check_in'] = attendance_type.check_out.value
        ctx['is_complete_attendance'] = True if att.check_in and att.check_out else False
    else:
        ctx['is_check_in'] = attendance_type.check_in.value
    return render(request, 'employee/attendance-info.html', ctx)


def regularization_required_attendance(request,company_id, company_staff_id):
    company_staff = CompanyStaff.objects.get(id=company_staff_id)
    atts = Attendance.objects.filter(employee=company_staff.employee)
    if atts:
        for att in atts:
            if att.regularization_required == False:
                atts = atts.exclude(id=att.id)
    print(atts)
    return render(request,'employee/regularization.html',context={'atts':atts, 'rassigne': Manager.objects.filter(user__company__id=company_id),'company_id':company_id, 'company_staff_id':company_staff_id})


def attendance_post(request,company_id, company_staff_id):
    if company_id:
        try:
            is_check_in = request.POST['is_check_in']
            attendance_id = request.POST['attendance_id']
            attendance_obj = Attendance.objects.filter(id=attendance_id).first() if attendance_id else Attendance()
            if is_check_in == attendance_type.check_in.value:
                attendance_obj.check_in = datetime.now()
            else:
                attendance_obj.check_out = datetime.now()
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            attendance_obj.employee = company_staff.employee
            attendance_obj.save()
            return JsonResponse({'status': 'SUCCESS'}, status=200)
        except Exception as e:
            return JsonResponse({'status': "FAILED"}, status=500)


def attendance_grid_data(request,company_id, company_staff_id):
    if company_id:
        grid_columns = ('check_in', 'check_out')
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        attendance_list = Attendance.objects.filter(employee=company_staff.employee)
        sort_column = grid_columns[int(request.GET['order[0][column]'])]
        ctx = getgriddatapaginated(request, attendance_list, sort_column)
        ctx['company_id'] = company_id
        ctx['company_staff_id'] = company_staff_id
        json_data = []
        for item in ctx['data']:
            dict = {}
            dict['check_in'] = item.check_in.strftime("%Y-%m-%d %H:%M:%S")
            if item.check_out:
                dict['check_out'] = item.check_out.strftime("%Y-%m-%d %H:%M:%S")
                dict['working_hours'] = strfdelta((item.check_out - item.check_in), "{hours}:{minutes}")
            else:
                dict['check_out'] = ''
                dict['working_hours'] = ''
            json_data.append(dict)
        ctx['data'] = json_data
        return ajax_response(ctx)


def taskList(request,company_id, company_staff_id):
    context ={}

    company_staff = CompanyStaff.objects.get(id=company_staff_id)

    queryset = MTask.objects.filter(assigned_to=company_staff.employee)
    print('queryset: ', queryset)
    context['tasks']= queryset
    context['company_id']= company_id
    context['company_staff_id']= company_staff_id
    return render(request, 'employee/my-project.html', context)


def SalaryListView(request,company_id, company_staff_id):
    context ={}

    company_staff = CompanyStaff.objects.get(id=company_staff_id)

    queryset = Salary.objects.filter(employee=company_staff.employee)
    print('queryset: ', queryset)
    context['salary']= queryset
    context['company_id']= company_id
    context['company_staff_id']= company_staff_id
    return render(request, 'employee/salary.html', context)


def notifications(request,company_id, company_staff_id):
    if company_id:
        notify = notification.objects.filter(company__id=company_id)
        context = {
            'notify': notify,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'employee/notifications.html', context)


def resign_creation(request):
    if request.method == 'POST':
        form = ResignCreationForm(data=request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            user = request.user
            instance.user = user
            instance.save()

            # print(instance.defaultdays)
            messages.success(request, 'Resignation Request Sent,wait for response',
                             extra_tags='alert alert-success alert-dismissible show')
            return redirect('/employee/resign/view/table/')

        messages.error(request, 'failed to Request a Resignation,please check entry dates',
                       extra_tags='alert alert-warning alert-dismissible show')
        return redirect('/employee/resign/')

    dataset = dict()
    form = ResignCreationForm()
    dataset['form'] = form
    dataset['title'] = 'Apply for Resignation'
    return render(request, 'employee/apply-resignation.html', dataset)


def view_my_resign_table(request,company_id, company_staff_id):
    # work on the logics
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        user = company_staff.employee
        resign = Resign.objects.filter(user=user)
        employee = Employee.objects.filter(user__company__id=company_id).first()
        dataset = dict()
        dataset['resign_list'] = resign
        dataset['employee'] = employee
        dataset['title'] = 'Resign List'
        dataset['company_id'] = company_id
        dataset['company_staff_id'] = company_staff_id
    else:
        return redirect('accounts:login')
    return render(request, 'employee/resignation-status.html', dataset)


class ResignRemove(View):
    def get(self, request, id):
        resign = Resign.objects.get(id=id)
        resign.delete()
        return HttpResponseRedirect('/employee/employee_dashboard/')


def holidays(request,company_id, company_staff_id):
    if company_id:
        holyday = holiday.objects.filter(company_id=company_id)
        context = {
            'holyday': holyday,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'employee/holiday.html', context)


def getfile(request):
    return serve(request, 'File')


class UserPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'employee/user_posts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 2

    def get_queryset(self):
        queryset = super(UserPostListView, self).get_queryset()
        queryset = Post.objects.filter(user=self.request.user.employee)
        return queryset


class PostDetailView(DetailView):
    model = Post
    template_name = 'employee/post_detail.html'


class PostCreateView(CreateView):
    model = Post
    template_name = 'employee/post_form.html'
    fields = ['experience_letter', 'offer_letter', 'education_certificate', 'skill_certificate', ]

    def form_valid(self, form):
        form.instance.user = self.request.user.employee
        return super().form_valid(form)


class PostUpdateView(UpdateView):
    model = Post
    template_name = 'employee/post_form.html'
    fields = ['file']

    def form_valid(self, form):
        form.instance.user = self.request.user.employee
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.user.employee:
            return True
        return False


class PostDeleteView(DeleteView):
    model = Post
    success_url = '/employee/post/new/'
    template_name = 'employee/post_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.user.employee:
            return True
        return False


def BalanceLeaveView(request,company_id, company_staff_id):
    context ={}

    company_staff = CompanyStaff.objects.get(id=company_staff_id)

    queryset = BalanceLeaves.objects.filter(user=company_staff.employee)
    print('queryset: ', queryset)
    context['balance']= queryset
    context['company_id']= company_id
    context['company_staff_id']= company_staff_id
    return render(request, 'employee/leave-balance.html', context)


def regularization(request):
    if request.method == 'POST':
        form = RegularizationCreationForm(data=request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            user = request.user.employee
            instance.user = user
            instance.save()

            # print(instance.defaultdays)
            messages.success(request, 'Apply for regularization Request Sent,wait for response',
                             extra_tags='alert alert-success alert-dismissible show')
            return redirect('/employee/regularization/view/table/')

        messages.error(request, 'failed to Request a Regularizations,please check entry dates',
                       extra_tags='alert alert-warning alert-dismissible show')
        return redirect('/employee/regularization/')

    dataset = dict()
    form = RegularizationCreationForm()
    dataset['form'] = form
    dataset['title'] = 'Apply for Regularization'
    return render(request, 'employee/regularization.html', dataset)


def regularization_table(request,company_id, company_staff_id):
    context ={}

    company_staff = CompanyStaff.objects.get(id=company_staff_id)

    queryset = Regularization.objects.filter(user=company_staff.employee)
    print('queryset: ', queryset)
    context['regularization']= queryset
    context['company_id']= company_id
    context['company_staff_id']= company_staff_id
    return render(request, 'employee/attendance-status.html', context)


def EntriesCreateView(request):
    if request.method == 'POST':
        form = EntryCreationForm(data=request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            user = request.user.employee
            instance.user = user
            instance.save()
            return redirect('/employee/entries-detail/')

        return redirect('/employee/entries-detail/')

    dataset = dict()
    form = EntryCreationForm()
    dataset['form'] = form
    dataset['title'] = 'Entry'
    return render(request, 'employee/create-timesheet.html', dataset)


def EntryDetailView(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        entry_obj_id = data.get('id', None)
        entry_obj = Entries.objects.get(pk=entry_obj_id)
        return JsonResponse(entry_obj.to_json())

    # work on the logics
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        user = company_staff.employee
        entry = Entries.objects.filter(user=user)

        dataset = dict()
        dataset['entry_list'] = entry
        dataset['title'] = 'Entry List'
        dataset['company_id'] = company_id
        dataset['company_staff_id'] = company_staff_id
    else:
        return redirect('accounts:login')
    return render(request, 'employee/view-timesheet.html', dataset)


class EntryRemove(View):
    def get(self, request,company_id, company_staff_id, id):
        if company_id:
            entry = Entries.objects.get(id=id)
            entry.delete()
            return redirect(f'/employee/entries-detail/{company_id}/{company_staff_id}')


class documents(generic.CreateView):
    model = Entries
    fields = ('title', 'start_time', 'end_time', 'project', 'activity', 'assigned_to')
    context_object_name = "entri_list"
    template_name = "employee/create-timesheet.html"
    success_url = ('/employee/entries-detail/')


def create_entry(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            project = request.POST.get("project")
            activity = request.POST.get("activity")
            assign_id = request.POST.get("manager_id")
            assigned_to = Manager.objects.get(id =assign_id)
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff
            emp = Employee.objects.get(user = user)

            Entries.objects.create(user = emp, start_time=start_time,end_time=end_time,project=project,activity=activity,assigned_to=assigned_to)
            return redirect(f'/employee/entries-detail/{company_id}/{company_staff_id}')

        else:
            return render(request,"employee/create-timesheet.html",{'assigned':Manager.objects.filter(user__company__id=company_id),'company_id':company_id, 'company_staff_id':company_staff_id})


def create_leave(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            startdate = request.POST.get("startdate")
            enddate   = request.POST.get("enddate")
            leavetype   = request.POST.get("leavetype")
            reason = request.POST.get("reason")
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff.employee
            # emp = User.objects.get(email=user)

            Leave.objects.create(user = user,startdate=startdate,enddate=enddate,leavetype=leavetype,reason=reason)
            return redirect(f'/employee/create_leave/{company_id}/{company_staff_id}')

        else:
            return render(request,"employee/apply-leaves.html",{'leavetypes': Leave.objects.all(),'company_id':company_id, 'company_staff_id':company_staff_id})


def create_resign(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            startdate = request.POST.get("startdate")
            reason= request.POST.get("reason")

            assign = request.POST.get("manager_id")
            assigned_too = Manager.objects.get(id =assign)
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff
            emp = Employee.objects.get(user = user)

            Resign.objects.create(user = emp, startdate=startdate,reason=reason,assigned_too=assigned_too)
            return redirect(f'/employee/create_resign/{company_id}/{company_staff_id}')

        else:
            return render(request,"employee/apply-resignation.html",{'rassigned':Manager.objects.filter(user__company__id=company_id),'company_id':company_id, 'company_staff_id':company_staff_id})


def create_regularization(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            print('request: ',request.POST)
            check_in = request.POST.get("check_in")
            check_out = request.POST.get("check_out")

            reason = request.POST.get("reason")
            assign_i = request.POST.get("manager_id")
            assigned_t = Manager.objects.get(id=assign_i)
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff
            emp = Employee.objects.get(user=user)

            Regularization.objects.create(user = emp, check_in=check_in,check_out=check_out,reason=reason,r_assigned_to=assigned_t)
            return redirect(f'/employee/regularization_required/{company_id}/{company_staff_id}')


        else:
            return render(request,"employee/regularization.html",{'rassigne':Manager.objects.filter(user__company__id=company_id),'company_id':company_id, 'company_staff_id':company_staff_id})


def create_ducuments(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            experience_letter = request.POST.get("experience_letter")
            offer_letter = request.POST.get("offer_letter")
            education_certificate  = request.POST.get("education_certificate")
            skill_certificate = request.POST.get("skill_certificate")
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff
            emp = Employee.objects.get(user=user)
            Post.objects.create(user = emp ,experience_letter=experience_letter,offer_letter=offer_letter,education_certificate=education_certificate,skill_certificate=skill_certificate)
            return redirect(f'/employee/employee_profile/{company_id}/{company_staff_id}')

        else:
            return render(request,"employee/my-profile.html",{'company_id':company_id, 'company_staff_id':company_staff_id})


def All_document_View(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        document_obj_id = data.get('id', None)
        document_obj = Post.objects.get(pk=document_obj_id)
        return JsonResponse(document_obj.to_json())

    # Old Code
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        document_list = Post.objects.filter(user=company_staff.employee)
        return render(request, 'employee/view_documents.html',
                      {'document_list': document_list,'company_id':company_id, 'company_staff_id':company_staff_id})


def ChangePassword(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            password = request.POST["password"]
            new_pas = request.POST["npwd"]

            user = CompanyStaff.objects.get(id=company_staff_id)
            un = user.email
            # check = user.check_password(current)
            check=check_password(password, user.password)
            if check == True:
                user.password=make_password(new_pas)
                user.save()
                messages.success(request, 'Password changed Successfully')
                return redirect('/')

        return render(request,"employee/change_password.html",{'company_id':company_id, 'company_staff_id':company_staff_id})

from django.contrib.auth.hashers import check_password, make_password
from django.http.response import HttpResponseRedirect
import json
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.views.generic import View

from account.models import CompanyStaff
from administration.models import Task, notification, holiday, MTask, Asign
from employee.models import Attendance, Entries, Employee
from leave.forms import LeaveCreationForm
from leave.models import Leave
from manager_leave.models import ManagerLeave
from manager_resign.models import ManagerResign
from managerpayroll.models import Salary
from manageregularization.forms import RegularizationCreationForm
from manageregularization.models import MRegularization
from regularization.models import Regularization
from resign.forms import ResignCreationForm
from resign.models import Resign
from .helpers.enum import attendance_type
from .helpers.helper import getgriddatapaginated, strfdelta, ajax_response
from django.contrib import messages
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from django.contrib.staticfiles.views import serve
from django.db.models import Q
from .models import Manager, ManagerAttendance, ManagerPost
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
User = get_user_model()


def manager_profile_view(request,company_id, company_staff_id):

    company_staff = CompanyStaff.objects.get(id=company_staff_id)
    profile = Manager.objects.filter(user=company_staff).first()
    if company_id:
        if request.method == "POST":
            data = dict(request.POST.copy())
            for field, value in data.items():
                if field != 'csrfmiddlewaretoken' and field != 'manager_image':
                    setattr(profile, field, value[0])

            if 'manager_image' in request.FILES:
                profile.manager_image = request.FILES['manager_image']

            profile.save()
        return render(request, 'managers/my-profile.html', {'profile': profile,'company_id': company_id, 'company_staff_id': company_staff_id})
    return render(request, 'managers/my-profile.html', {'profile': profile},{'company_id':company_id, 'company_staff_id':company_staff_id})


# def manager_profile_view(request,company_id, company_staff_id):
#
#     company_staff = CompanyStaff.objects.get(id=company_staff_id)
#     profile = Manager.objects.filter(user=company_staff).first()
#     if company_id:
#         if request.method == "POST":
#             data = dict(request.POST.copy())
#             for field, value in data.items():
#                 if field != 'csrfmiddlewaretoken' and field != 'manager_image':
#                     setattr(profile, field, value[0])
#
#             if 'manager_image' in request.FILES:
#                 profile.manager_image = request.FILES['manager_image']
#
#             profile.save()
#
#             return render(request, 'managers/my-profile.html', {'profile': profile},{'company_id':company_id, 'company_staff_id':company_staff_id})
#     return render(request, 'managers/my-profile.html',
#                   {'company_id': company_id, 'company_staff_id': company_staff_id})


class managerUpdateView(UpdateView):
    model = Manager
    template_name = 'managers/my-profile.html'
    fields = '__all__'
    context_object_name = 'manager_update'


def ManagerDashboardView(request,company_id, company_staff_id):
    ctx = {}
    today = datetime.now().date()
    tomorrow = today + timedelta(1)

    company_staff = CompanyStaff.objects.get(id=company_staff_id)
    att = ManagerAttendance.objects.filter(Q(check_in__gt=today)
                                           & Q(check_in__lt=tomorrow)
                                           & Q(manager=company_staff.manager)).first()
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
    return render(request, "managers/index.html", ctx)


def leave_creation(request,company_id, company_staff_id):
    if company_id:
        if request.method == 'POST':
            form = LeaveCreationForm(data=request.POST)
            if form.is_valid():
                instance = form.save(commit=False)
                company_staff = CompanyStaff.objects.get(id=company_staff_id)
                user = company_staff
                instance.user = user
                instance.save()
                messages.success(request, 'Leave Request Sent,wait for response',
                                 extra_tags='alert alert-success alert-dismissible show')
                return redirect('/managers/mleaves/view/table/')

            messages.error(request, 'failed to Request a Leave,please check entry dates',
                           extra_tags='alert alert-warning alert-dismissible show')
            return redirect(f'/managers/leave/{company_id}/{company_staff_id}')

        dataset = dict()
        form = LeaveCreationForm()
        dataset['form'] = form
        dataset['title'] = 'Apply for Leave'
        dataset['company_id'] = company_id
        dataset['company_staff_id'] = company_staff_id
        return render(request, 'managers/apply-leave.html', dataset)


#  staffs leaves table user only
def view_my_leave_table(request,company_id, company_staff_id):
    # work on the logics
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        user = company_staff.manager
        leaves = ManagerLeave.objects.filter(user=user)
        # manager = Manager.objects.filter(user=user.manager_email).first()
        dataset = dict()
        dataset['leave_list'] = leaves
        # dataset['manager'] = manager
        dataset['title'] = 'Leaves List'
        dataset['company_id'] = company_id
        dataset['company_staff_id'] = company_staff_id
    else:
        return redirect('accounts:login')
    return render(request, 'managers/leave-status.html', dataset)


class LeaveRemove(View):
    def get(self, request, id):
        leave = Leave.objects.get(id=id)
        leave.delete()
        return HttpResponseRedirect('/managers/manager_dashboard/')


def BalanceLeaveView(request,company_id, company_staff_id):
    context ={}

    company_staff = CompanyStaff.objects.get(id=company_staff_id)

    queryset = ManagerLeave.objects.filter(user=company_staff.manager)
    print('queryset: ', queryset)
    context['balance']= queryset
    context['company_id']= company_id
    context['company_staff_id']= company_staff_id
    return render(request, 'managers/leave-balance.html', context)

# class BalanceLeaveView(ListView, LoginRequiredMixin):
#     model = ManagerLeave
#     template_name = 'managers/leave-balance.html'
#     order = ['-created_date', 'name']
#     context_object_name = 'balance'
#
#     def get_queryset(self):
#         queryset = super(BalanceLeaveView, self).get_queryset()
#         queryset = ManagerLeave.objects.filter(user=self.request.user.manager)
#         return queryset


def attendance(request,company_id, company_staff_id):
    ctx = {}
    today = datetime.now().date()
    tomorrow = today + timedelta(1)

    company_staff = CompanyStaff.objects.get(id=company_staff_id)
    att = ManagerAttendance.objects.filter(Q(check_in__gt=today)
                                           & Q(check_in__lt=tomorrow)
                                           & Q(manager=company_staff.manager)).first()
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
    return render(request, 'managers/attendance-info.html', ctx)


def regularization_required_attendance(request,company_id, company_staff_id):
    company_staff = CompanyStaff.objects.get(id=company_staff_id)
    atts = ManagerAttendance.objects.filter(manager=company_staff.manager)
    if atts:
        for att in atts:
            if att.regularization_required == False:
                atts = atts.exclude(id=att.id)
    print(atts)
    return render(request, 'managers/regularization.html', context={'atts': atts,'company_id':company_id, 'company_staff_id':company_staff_id})


def attendance_post(request,company_id, company_staff_id):
    if company_id:
        try:
            is_check_in = request.POST['is_check_in']
            attendance_id = request.POST['attendance_id']
            attendance_obj = ManagerAttendance.objects.filter(
                id=attendance_id).first() if attendance_id else ManagerAttendance()
            if is_check_in == attendance_type.check_in.value:
                attendance_obj.check_in = datetime.now()
            else:
                attendance_obj.check_out = datetime.now()
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            attendance_obj.manager = company_staff.manager
            attendance_obj.save()
            return JsonResponse({'status': 'SUCCESS'}, status=200)
        except Exception as e:
            return JsonResponse({'status': "FAILED"}, status=500)


def attendance_grid_data(request,company_id, company_staff_id):
    if company_id:
        grid_columns = ('check_in', 'check_out')
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        attendance_list = ManagerAttendance.objects.filter(manager=company_staff.manager)
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

def SalaryListView(request,company_id, company_staff_id):
    context ={}

    company_staff = CompanyStaff.objects.get(id=company_staff_id)

    queryset = Salary.objects.filter(manager=company_staff.manager)
    print('queryset: ', queryset)
    context['salary']= queryset
    context['company_id']= company_id
    context['company_staff_id']= company_staff_id
    return render(request, 'managers/salary.html', context)

# class SalaryListView(ListView, LoginRequiredMixin):
#     model = Salary
#     template_name = 'managers/salary.html'
#     order = ['-created_date', 'name']
#     context_object_name = 'salary'
#
#     def get_queryset(self):
#         manager = get_object_or_404(Manager, user=self.request.user)
#         return Salary.objects.filter(manager=manager)
#

def notifications(request,company_id, company_staff_id):
    if company_id:
        notify = notification.objects.filter(company__id=company_id)
        context = {
            'notify': notify,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'managers/notifications.html', context)


def resign_creation(request):
    if request.method == 'POST':
        form = ResignCreationForm(data=request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            user = request.user
            instance.user = user
            instance.save()

            messages.success(request, 'Resignation Request Sent,wait for response',
                             extra_tags='alert alert-success alert-dismissible show')
            return redirect('/managers/mresign/view/table/')

        messages.error(request, 'failed to Request a Resignation,please check entry dates',
                       extra_tags='alert alert-warning alert-dismissible show')
        return redirect('/managers/resign/')

    dataset = dict()
    form = ResignCreationForm()
    dataset['form'] = form
    dataset['title'] = 'Apply for Resignation'
    return render(request, 'managers/apply-resignation.html', dataset)


def view_my_resign_table(request,company_id, company_staff_id):
    # work on the logics
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        user = company_staff.manager
        resign = ManagerResign.objects.filter(user=user)
        manager = Manager.objects.filter(user__company__id=company_id).first()
        dataset = dict()
        dataset['resign_list'] = resign
        dataset['manager'] = manager
        dataset['title'] = 'Resign List'
        dataset['company_id'] = company_id
        dataset['company_staff_id'] = company_staff_id
    else:
        return redirect('accounts:login')
    return render(request, 'managers/resignation-status.html', dataset)


class ResignRemove(View):
    def get(self, request, id):
        resign = Resign.objects.get(id=id)
        resign.delete()
        return HttpResponseRedirect('/managers/manager_dashboard/')



def holidays(request,company_id, company_staff_id):
    if company_id:
        holyday = holiday.objects.filter(company_id=company_id)
        context = {
            'holyday': holyday,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'managers/holiday.html', context)



def getfile(request):
    return serve(request, 'File')


class PostListView(ListView):
    model = ManagerPost
    template_name = 'managers/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 2


class UserPostListView(LoginRequiredMixin, ListView):
    model = ManagerPost
    template_name = 'managers/my-profile.html'
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = super(UserPostListView, self).get_queryset()
        queryset = ManagerPost.objects.filter(user=self.request.user)
        return queryset


class PostDetailView(DetailView):
    model = ManagerPost
    template_name = 'managers/post_detail.html'
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = super(PostDetailView, self).get_queryset()
        queryset = ManagerPost.objects.filter(user=self.request.user.manager)
        return queryset


class PostCreateView(CreateView):
    model = ManagerPost
    template_name = 'managers/post_form.html'
    fields = ['experience_letter', 'offer_letter', 'education_certificate', 'skill_certificate', ]

    def form_valid(self, form):
        form.instance.user = self.request.user.manager
        return super().form_valid(form)


class PostUpdateView(UpdateView):
    model = ManagerPost
    template_name = 'managers/post_form.html'
    fields = ['file']

    def form_valid(self, form):
        form.instance.user = self.request.user.manager
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.user.manager:
            return True
        return False


class PostDeleteView(DeleteView):
    model = ManagerPost
    success_url = '/managers/manager_dashboard/'
    template_name = 'managers/view_documents.html'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.user.manager:
            return True
        return False

    # def get_queryset(self):
    #     user = get_object_or_404(User, user=self.request.user)
    #     return Leave.objects.filter(user=user).order_by('-created_date')


def mregularization(request):
    if request.method == 'POST':
        form = RegularizationCreationForm(data=request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            user = request.user.manager
            instance.user = user
            instance.save()

            messages.success(request, 'Apply for regularization Request Sent,wait for response',
                             extra_tags='alert alert-success alert-dismissible show')
            return redirect('/managers/attendanc/')

        messages.error(request, 'failed to Request a Regularizations,please check entry dates',
                       extra_tags='alert alert-warning alert-dismissible show')
        return redirect('/managers/mregularizations/')

    dataset = dict()
    form = RegularizationCreationForm()
    dataset['form'] = form
    dataset['title'] = 'Apply for Regularization'
    return render(request, 'managers/regularization.html', dataset)


def view_my_regularization_table(request,company_id, company_staff_id):
    # work on the logics
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        user = company_staff.manager
        regularization = MRegularization.objects.filter(user=user)
        dataset = dict()
        dataset['regularization_list'] = regularization
        dataset['title'] = 'regularization List'
        dataset['company_id'] = company_id
        dataset['company_staff_id'] = company_staff_id
    else:
        return redirect('accounts:login')
    return render(request, 'managers/attendance-status.html', dataset)


class TaskCreateViews(CreateView, LoginRequiredMixin):
    model = MTask
    fields = ['title', 'description', 'assigned_to']

    def form_valid(self, form):
        form.instance.created_by = self.request.user.email
        return super().form_valid(form)


class TaskDetailViews(DetailView, LoginRequiredMixin):
    model = MTask
    template_name = "managers/task_detail.html"


class TaskDeleteViews(DeleteView, LoginRequiredMixin, UserPassesTestMixin):
    model = MTask
    success_url = '/managers/dashboard/'

    def test_func(self):
        task = self.get_object()
        return self.request.user == task.created_by


def Project_list(request,company_id, company_staff_id):
    if company_id:
        project = MTask.objects.filter(assigned_to__user__company__id=company_id)
        context = {
            'project': project,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'managers/list-project.html', context)


class ProjectRemove(View):
    def get(self, request, id):
        project = MTask.objects.get(id=id)
        project.delete()
        return HttpResponseRedirect('/managers/mprojectlist/')


def TaskListView(request,company_id, company_staff_id):
    context ={}

    company_staff = CompanyStaff.objects.get(id=company_staff_id)

    queryset = Task.objects.filter(assigned_to=company_staff.manager)
    print('queryset: ', queryset)
    context['tasks']= queryset
    context['company_id']= company_id
    context['company_staff_id']= company_staff_id
    return render(request, 'managers/my-project.html', context)

# class TaskListView(ListView, LoginRequiredMixin):
#     model = Task
#     template_name = 'managers/my-project.html'
#     order = ['-created_date', 'name']
#     context_object_name = 'tasks'
#
#     def get_queryset(self):
#         queryset = super(TaskListView, self).get_queryset()
#         queryset = Task.objects.filter(assigned_to=self.request.user.manager)
#         return queryset
#

def attendanc(request,company_id, company_staff_id):
    if company_id:
        attendance = Attendance.objects.filter(employee__user__company__id=company_id)
        context = {
            'attendance': attendance,
            'company_id': company_id,
            'company_staff_id':company_staff_id,

        }
    return render(request, 'managers/attendance-list.html',context)


def mattendance_Edit_View(request,company_id, company_staff_id):
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

            print('attendance id is-')
            print(emp_id)
            return redirect(f'/managers/mnattendancee/{company_id}/{company_staff_id}')


class AttendanceRemove(View):
    def get(self, request, id):
        attendance = Attendance.objects.get(id=id)
        attendance.delete()
        messages.success(request, f"{attendance} deleted successfully")
        return HttpResponseRedirect('/managers/mnattendancee/')


class AttendanceManage(UpdateView):
    model = Attendance
    fields = ['check_in', 'check_out']
    context_object_name = "attendance_update"
    template_name = "managers/attendance_manage.html"
    success_url = ("/managers/attendanc/")

    def post(self, request, pk):
        data = Attendance.objects.get(id=pk)
        data.check_out = request.POST.get('check_out')
        data.check_in = request.POST.get('check_in')
        data.save()
        print(str(data) + "=" + str(request.POST.get('check_out')))
        return HttpResponseRedirect("/managers/mnattendancee/")


# def Attendancesearch(request):
#     template = 'managers/attendancelist.html'
#
#     query = request.GET.get('q')
#
#     result = Attendance.objects.filter(
#         Q(employee__employee_email__icontains=query))
#     context = {'attendance': result}
#     return render(request, template, context)

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
    return render(request, 'managers/attendance-list.html', context)

# class regularization_list(View):
#     def get(self,request):
#         if request.method == "POST":
#             data = json.loads(request.body.decode('utf-8'))
#             regularization_obj_id = data.get('id', None)
#             regularization_obj = Regularization.objects.get(pk=regularization_obj_id)
#             return JsonResponse(regularization_obj.to_json())
#
#         # regularization = Regularization.objects.all_pending_regularization()
#         regularization = Regularization.objects.filter(r_assigned_to=self.request.user.manager)
#         return render(request, 'managers/pending-regularization.html',
#                       {'regularization_list': regularization, 'title': 'regularization list - pending'})


def regularization_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = Regularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        regularization = Regularization.objects.all_pending_regularization().filter(r_assigned_to=company_staff.manager)
        return render(request, 'managers/pending-regularization.html',{'regularization_list': regularization, 'title': 'regularization list - pending','company_id':company_id, 'company_staff_id':company_staff_id})


# class regularization_list(ListView, LoginRequiredMixin):
#     model = Regularization
#     template_name = 'managers/pending-regularization.html'
#     order = ['-created_date', 'name']
#     context_object_name = 'regularization'
#
#     def get_queryset(self):
#         queryset = super(regularization_list, self).get_queryset()
#         queryset = Regularization.objects.filter(r_assigned_to=self.request.user.manager)
#         return queryset


def regularization_approved_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = Regularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
    regularization = Regularization.objects.all_approved_regularization().filter(r_assigned_to=company_staff.manager) # approved leaves -> calling model manager method
    return render(request, 'managers/approved-regularization.html',
                  {'regularization_list': regularization, 'title': 'approved regularization list','company_id':company_id, 'company_staff_id':company_staff_id})


def regularization_view(request, id):
    if not request.user.is_staff:
        return redirect('/')

    regularization = get_object_or_404(Regularization, id=id)
    # employee = Employee.objects.filter(user=regularization.user.employee)[0]
    # print(employee)
    return render(request, 'managers/regularization_detail_view.html',
                  {'regularization': regularization, 'attendance': attendance,
                   'title': '{0}-{1} regularization'.format(
                       regularization.user.employee_email,
                       regularization.status)})


def approve_regularization(request,company_id, company_staff_id,id):
    if company_id:
        regularization = get_object_or_404(Regularization, id=id)

        regularization.approve_regularization

        messages.error(request, 'regularizationation successfully approved',
                       extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/managers/mnregularization/approved/all/{company_id}/{company_staff_id}')


def cancel_regularization_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        regularization_obj_id = data.get('id', None)
        regularization_obj = Regularization.objects.get(pk=regularization_obj_id)
        return JsonResponse(regularization_obj.to_json())

    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
    regularization = Regularization.objects.all_cancel_regularization().filter(r_assigned_to=company_staff.manager)
    return render(request, 'managers/cancelled-regularization.html',
                  {'regularization_list_cancel': regularization, 'title': 'Cancel regularization list','company_id':company_id, 'company_staff_id':company_staff_id})


def unapprove_regularization(request, id):
    if not request.user.is_staff:
        return redirect('/')
    regularization = get_object_or_404(Regularization, id=id)
    regularization.unapprove_regularization
    return redirect('mnregularizationlist')  # redirect to unapproved list


def cancel_regularization(request,company_id, company_staff_id,id):
    if company_id:
        regularization = get_object_or_404(Regularization, id=id)
        regularization.regularization_cancel

        messages.success(request, 'regularization is canceled', extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/managers/mnregularization/cancel/all/{company_id}/{company_staff_id}')


# Current section -> here
def uncancel_regularization(request, id):
    if not request.user.is_staff:
        return redirect('/')
    regularization = get_object_or_404(Regularization, id=id)
    regularization.status = 'pending'
    regularization.is_approved = False
    regularization.save()
    messages.success(request, 'Regulaization is uncanceled,now in pending list',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('mncancelregularizationlist')


def regularization_rejected_list(request):
    dataset = dict()
    regularization = Regularization.objects.all_rejected_regularization()

    dataset['regularization_list_rejected'] = regularization
    return render(request, 'managers/rejected_regularization_list.html', dataset)


def reject_regularization(request, id):
    dataset = dict()
    regularization = get_object_or_404(Leave, id=id)
    regularization.reject_leave
    messages.success(request, 'regularizationation is rejected',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('mnregularizationrejected')


def unreject_regularization(request, id):
    regularization = get_object_or_404(Regularization, id=id)
    regularization.status = 'pending'
    regularization.is_approved = False
    regularization.save()
    messages.success(request, 'regularizationation is now in pending list ',
                     extra_tags='alert alert-success alert-dismissible show')

    return redirect('mnregularizationrejected')

def AssignListView(request,company_id, company_staff_id):
    context ={}

    company_staff = CompanyStaff.objects.get(id=company_staff_id)

    queryset = Asign.objects.filter(assigned_to=company_staff.manager)
    print('queryset: ', queryset)
    context['assign']= queryset
    context['company_id']= company_id
    context['company_staff_id']= company_staff_id
    return render(request, 'managers/list-employee.html', context)

# class AssignListView(ListView, LoginRequiredMixin,):
#     model = Asign
#     template_name = 'managers/list-employee.html'
#     order = ['-created_date', 'name']
#     context_object_name = 'assign'
#
#     def get_queryset(self,company_id, company_staff_id):
#         queryset = super(AssignListView, self).get_queryset(company_id, company_staff_id)
#         company_staff = CompanyStaff.objects.get(id=company_staff_id)
#         queryset = Asign.objects.filter(assigned_to=company_staff.manager)
#         return queryset


def EntryListView(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        entry_obj_id = data.get('id', None)
        entry_obj = Entries.objects.get(pk=entry_obj_id)
        return JsonResponse(entry_obj.to_json())
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        entry = Entries.objects.filter(assigned_to=company_staff.manager)
        context = {
            'entry': entry,
            'company_id': company_id,
            'company_staff_id': company_staff_id,

        }
        return render(request, 'managers/employee-timesheet.html', context)

# class EntryListView(ListView, LoginRequiredMixin):
#     model = Entries
#     template_name = 'managers/employee-timesheet.html'
#     order = ['-created_date', 'name']
#     context_object_name = 'entry'
#
#     def get_queryset(self):
#         queryset = super(EntryListView, self).get_queryset()
#         queryset = Entries.objects.filter(assigned_to=self.request.user.manager)
#         return queryset


class EntryRemove(View):
    def get(self, request, id):
        entry = Entries.objects.get(id=id)
        entry.delete()
        return HttpResponseRedirect('/managers/entry-list/')


def create_ducument(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            experience_letter = request.POST.get("experience_letter")
            offer_letter = request.POST.get("offer_letter")
            education_certificate = request.POST.get("education_certificate")
            skill_certificate = request.POST.get("skill_certificate")
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff
            emp = Manager.objects.get(user=user)
            ManagerPost.objects.create(user=emp, experience_letter=experience_letter, offer_letter=offer_letter,
                                       education_certificate=education_certificate, skill_certificate=skill_certificate)
            return redirect(f'/managers/manager_profile/{company_id}/{company_staff_id}')

        else:
            return render(request, "managers/my-profile.html",{'company_id':company_id, 'company_staff_id':company_staff_id})


def create_mregularizations(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            check_in = request.POST.get("check_in")
            check_out = request.POST.get("check_out")

            reason = request.POST.get("reason")

            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff
            emp = Manager.objects.get(user=user)

            MRegularization.objects.create(user=emp, check_in=check_in, check_out=check_out, reason=reason)
            return redirect(f'/managers/mregularization_required/{company_id}/{company_staff_id}')

        else:
            return render(request, "managers/regularization.html", {'rassigne': Manager.objects.all()},{'company_id':company_id, 'company_staff_id':company_staff_id})


def add_project(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            title = request.POST.get("title")
            description = request.POST.get("description")

            assign_i = request.POST.get("employee_id")
            assigned_t = Employee.objects.get(id=assign_i)
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff
            emp = Manager.objects.get(user=user)

            MTask.objects.create(user=emp, title=title, description=description, assigned_to=assigned_t)
            return redirect(f'/managers/mprojectlist/{company_id}/{company_staff_id}')

        else:
            return render(request, "managers/add-project.html", {'addProject': Employee.objects.filter(user__company__id=company_id),'company_id':company_id, 'company_staff_id':company_staff_id})


def add_leave(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            startdate = request.POST.get("startdate")
            enddate = request.POST.get("enddate")
            leavetype = request.POST.get("leavetype")
            reason = request.POST.get("reason")
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff.manager
            # emp = User.objects.get(email=user)

            ManagerLeave.objects.create(user=user, startdate=startdate, enddate=enddate, leavetype=leavetype, reason=reason)
            return redirect(f'/managers/mleave/{company_id}/{company_staff_id}')

        else:
            return render(request, "managers/apply-leave.html", {'leavetypes': ManagerLeave.objects.all()},{'company_id':company_id, 'company_staff_id':company_staff_id})


def create_mresignation(request,company_id, company_staff_id):
    if company_id:
        if request.method == "POST":
            startdate = request.POST.get("startdate")

            reason = request.POST.get("reason")
            company_staff = CompanyStaff.objects.get(id=company_staff_id)
            user = company_staff
            emp = Manager.objects.get(user=user)

            ManagerResign.objects.create(user=emp, startdate=startdate, reason=reason)
            return redirect(f'/managers/create_mresignation/{company_id}/{company_staff_id}')

        else:
            return render(request, "managers/apply-resignation.html",{'company_id':company_id, 'company_staff_id':company_staff_id})


def resign_list(request,company_id, company_staff_id):
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        resign = Resign.objects.all_pending_resign().filter(assigned_too=company_staff.manager)
        return render(request, 'managers/employee-resignation.html',
                      {'resign_list': resign, 'title': 'resign list - pending','company_id':company_id, 'company_staff_id':company_staff_id})


def approve_resign(request,company_id, company_staff_id, id):
    if company_id:
        resign = get_object_or_404(Resign, id=id)
        # user = resign.user
        # employee = Employee.objects.filter(user=user)
        resign.approve_resign

        messages.error(request, 'Resignation successfully approved',
                       extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/managers/resign_list/{company_id}/{company_staff_id}')


def cancel_resign(request,company_id, company_staff_id, id):
    if company_id:
        resign = get_object_or_404(Resign, id=id)
        resign.resign_cancel

        messages.success(request, 'Resign is canceled', extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/managers/resign_list/{company_id}/{company_staff_id}')


def leave_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        leave_obj_id = data.get('id', None)
        leave_obj = Leave.objects.get(pk=leave_obj_id)
        return JsonResponse(leave_obj.to_json())

    if company_id:
        leaves = Leave.objects.all_pending_leaves().filter(user__user__company_id=company_id)
        return render(request, 'managers/employee-leaves.html',{'leave_list': leaves, 'title': 'leaves list - pending','company_id':company_id, 'company_staff_id':company_staff_id})



def leaves_approved_list(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        leave_obj_id = data.get('id', None)
        leave_obj = Leave.objects.get(pk=leave_obj_id)
        return JsonResponse(leave_obj.to_json())

    if company_id:
        leaves = Leave.objects.all_approved_leaves().filter(user__user__company_id=company_id)  # approved leaves -> calling model manager method
        return render(request, 'managers/approved-leaves.html',
                      {'leave_list': leaves, 'title': 'approved leave list','company_id':company_id, 'company_staff_id':company_staff_id})


def leaves_view(request, id):
    if not (request.user.is_authenticated):
        return redirect('/')

    leave = get_object_or_404(Leave, id=id)
    print(leave.user)

    return render(request, 'managers/leave_detail_view.html', {'leave': leave,
                                                                     'title': '{0}-{1} leave'.format(
                                                                         leave.user.username,
                                                                         leave.status)})


def approve_leave(request,company_id, company_staff_id, id):
    if company_id:

        leave = get_object_or_404(Leave, id=id)

        leave.approve_leave

        messages.error(request, 'Leave successfully approved',
                       extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/managers/leave_list/{company_id}/{company_staff_id}')


def cancel_leaves_list(request,company_id, company_staff_id):
    if company_id:
        leaves = Leave.objects.all_cancel_leaves().filter(user__user__company_id=company_id)
        return render(request, 'managers/cancelled-leaves.html',
                      {'leave_list_cancel': leaves, 'title': 'Cancel leave list','company_id':company_id, 'company_staff_id':company_staff_id})


def unapprove_leave(request, id):

    leave = get_object_or_404(Leave, id=id)
    leave.unapprove_leave
    return redirect('leave_list')  # redirect to unapproved list


def cancel_leave(request,company_id, company_staff_id, id):
    if company_id:
        leave = get_object_or_404(Leave, id=id)
        leave.leaves_cancel

        messages.success(request, 'Leave is canceled', extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/managers/leave_list/{company_id}/{company_staff_id}')


# Current section -> here
def uncancel_leave(request, id):

    leave = get_object_or_404(Leave, id=id)
    leave.status = 'pending'
    leave.is_approved = False
    leave.save()
    messages.success(request, 'Leave is uncanceled,now in pending list',
                     extra_tags='alert alert-success alert-dismissible show')
    return redirect('leave_list')  # work on redirecting to instance leave - detail view


def leave_rejected_list(request):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        leave_obj_id = data.get('id', None)
        leave_obj = Leave.objects.get(pk=leave_obj_id)
        return JsonResponse(leave_obj.to_json())

    dataset = dict()
    leave = Leave.objects.all_rejected_leaves()

    dataset['leave_list_rejected'] = leave
    return render(request, 'managers/rejected-leaves.html', dataset)


def reject_leave(request,company_id, company_staff_id, id):
    if company_id:
        dataset = dict()
        leave = get_object_or_404(Leave, id=id)
        leave.reject_leave
        messages.success(request, 'Leave is rejected', extra_tags='alert alert-success alert-dismissible show')
        return redirect(f'/managers/leave_list/{company_id}/{company_staff_id}')


def unreject_leave(request, id):
    leave = get_object_or_404(Leave, id=id)
    leave.status = 'pending'
    leave.is_approved = False
    leave.save()
    messages.success(request, 'Leave is now in pending list ', extra_tags='alert alert-success alert-dismissible show')

    return redirect('leavesrejected')


def All_document_Views(request,company_id, company_staff_id):
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        document_obj_id = data.get('id', None)
        document_obj = ManagerPost.objects.get(pk=document_obj_id)
        return JsonResponse(document_obj.to_json())

    # Old Code
    if company_id:
        company_staff = CompanyStaff.objects.get(id=company_staff_id)
        document_list = ManagerPost.objects.filter(user=company_staff.manager)
        return render(request, 'managers/view_documents.html', {'document_list': document_list,'company_id':company_id, 'company_staff_id':company_staff_id})


# def Attendancesearch(request):
#     if 'q' in request.GET:
#         q = request.GET['q']
#         multiple_q = Q(Q(employee__employee_email__icontains=q) | Q(check_in__icontains=q) | Q(check_out__icontains=q))
#         attendance = Attendance.objects.filter(multiple_q)
#     else:
#         attendance = Attendance.objects.all()
#     context = {
#         'attendance': attendance
#     }
#     return render(request, 'managers/attendance-list.html', context)


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

        return render(request,"managers/change_password.html",{'company_id':company_id, 'company_staff_id':company_staff_id})

# def ChangePassword(request):
#     if request.user.is_authenticated:
#         if request.method == 'POST':
#             current = request.POST["cpwd"]
#             new_pas = request.POST["npwd"]
#
#             user = User.objects.get(id=request.user.id)
#             un = user.email
#             check = user.check_password(current)
#             if check == True:
#                 user.set_password(new_pas)
#                 user.save()
#                 update_session_auth_hash(request, user)
#                 messages.success(request, 'Password changed Successfully')
#                 user = User.objects.get(email=un)
#                 login(request, user)
#                 return redirect('/')
#             else:
#                 messages.error(request, 'Incorrect Current Password')
#
#         return render(request, "managers/change_password.html")
#

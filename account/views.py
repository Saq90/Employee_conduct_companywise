# from groups_manager.models import Group,GroupType, Member
from account.forms import SignUpForm
from account.models import User, CompanyStaff, Company
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import user_passes_test, login_required
from django.utils.decorators import method_decorator
from employee.models import Department, Designation, Employee
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.urls import reverse_lazy
# from django.contrib.auth.models import Group, User
from django.views.generic import View, TemplateView, UpdateView
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
import sweetify
from django.core.mail import EmailMessage
import random


# Signs Up View

#
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('signin')
    template_name = 'account/signup.html'


class SignInView(View):
    def post(self, request):
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(username=email, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if user.groups.all().exists() or user.is_company_admin:
                    return HttpResponseRedirect('/administration/index')

                if user.is_staff:
                    return HttpResponseRedirect('/managers/dashboard')

                if user.is_employee:
                    return HttpResponseRedirect("/employee/employee_dashboard")

                else:
                    return HttpResponseRedirect(settings.LOGIN_URL)
            else:
                return HttpResponse("Inactive user.")
        else:

            return HttpResponseRedirect(settings.LOGIN_URL)

    def get(self, request):
        return render(request, "account/login.html")


class LogoutView(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGIN_URL)


# Role
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='post')
class RegisterRole(View):
    def post(self, request):
        role_name = request.POST['role']
        try:
            group = Group.objects.create(name=role_name)
            sweetify.success(self.request, f'{group} is created', button='Ok', timer=3000)
        except IntegrityError as e:
            sweetify.success(self.request, f"{group} is Already exist, button='Ok'", timer=3000)
        groups = Group.objects.all()
        return render(request, "account/role.html", {'groups': groups})

    def get(self, request):
        groups = Group.objects.all()
        return render(request, "account/role.html", {'groups': groups})


class RemoveRole(View):
    def get(self, request, name):
        try:

            groups = Group.objects.get(name=name)

            if User.objects.filter(groups__name=groups).exists():
                messages.error(request,
                               f'Cant delete {groups} ,Delete assigned Users  First and Try Again! <a href="/usertorole/{groups}"> click Here </a>',
                               extra_tags='safe')

            else:
                groups.delete()
                # messages.success(request,f"{groups} Deleted Successfully")
                sweetify.success(self.request, f'{groups} is Deleted', button='Ok', timer=3000)

        except Group.DoesNotExist:
            messages.error(request, "Role already Deleted or Not Created")
        return HttpResponseRedirect('/role')


class RemoveUserToRole(View):
    def get(self, request, name, id):
        role = Group.objects.get(name=name)
        user = User.objects.get(id=id)
        user.is_admin = False
        user.save()
        user.groups.remove(role)
        # messages.warning(request,f"{user} is removed from {role} ") 
        sweetify.info(self.request, f"{user} is removed from {role} ", button='Ok', timer=3000)
        return redirect('/usertorole/' + str(role))


class demoview(TemplateView):
    template_name = "account/demo.html"


class UserToRole(View):
    def get(self, request, name):
        role = Group.objects.get(name=name)
        employees = Employee.objects.all()
        role_user = User.objects.filter(groups__name=role)
        for user in role_user:
            user.is_admin = True
            user.save()
        return render(request, 'account/usertorole.html',
                      {'role': role, 'employees': employees, 'role_user': role_user
                       })

    def post(self, request, name):
        role = Group.objects.get(name=name)
        employe = request.POST['employee']
        user = User.objects.get(email=employe)
        userIngroup = user.groups.all().exists()

        if userIngroup != True:
            user.groups.add(role)
            # messages.info(request,f"Congratulation {user} become a {role} ")
            sweetify.success(self.request, f"Congratulation {user} become a {role} ", button='Ok', timer=3000)
        else:
            userInWhichgroup = user.groups.all()
            for userRole in userInWhichgroup:
                messages.warning(request, f"Sorry {user} is Already having {userRole} Role ")
        return redirect('/usertorole/' + str(role))


class RolePermissionView(View):
    def get(self, request, name):
        role = Group.objects.get(name=name)
        permissions = role.permissions.all()
        print(permissions)

        for permission in permissions:
            if permission.codename == 'view_employee':
                view_employee = 'True'
            else:
                view_employee = 'False'

            if permission.codename == 'add_employee':
                add_employee = 'True'
            else:
                add_employee = 'False'

            if permission.codename == 'change_employee':
                change_employee = 'True'
            else:
                change_employee = 'False'
            if permission.codename == 'delete_employee':
                delete_employee = 'True'
            else:
                delete_employee = 'False'
        # ______________employee end_________________________________________
        return render(request, 'account/add_roles_permission.html',
                      {'role': role,
                       # 'add_employee':add_employee,
                       # 'view_employee':view_employee,
                       # 'change_employee':change_employee,
                       # 'delete_employee':delete_employee

                       })

    def post(self, request, name):
        role = Group.objects.get(name=name)
        view_employee = request.POST['view_employee']
        add_employee = request.POST['add_employee']
        change_employee = request.POST['change_employee']
        delete_employee = request.POST['delete_employee']

        content_type = ContentType.objects.get_for_model(Employee, for_concrete_model=False)
        employee_permision = Permission.objects.filter(content_type=content_type)
        for permission in employee_permision:
            if permission.codename == 'view_employee':
                if view_employee == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'add_employee':
                if add_employee == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'change_employee':
                if change_employee == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'delete_employee':
                if delete_employee == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
        sweetify.info(self.request, 'Permision Granted', button='Ok', timer=3000)

        view_department = request.POST['view_department']
        add_department = request.POST['add_department']
        change_department = request.POST['change_department']
        delete_department = request.POST['delete_department']

        content_type = ContentType.objects.get_for_model(Department, for_concrete_model=False)
        department_permision = Permission.objects.filter(content_type=content_type)
        for permission in department_permision:
            if permission.codename == 'view_department':
                if view_department == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'add_department':
                if add_department == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'change_department':
                if change_department == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'delete_department':
                if delete_department == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
        sweetify.info(self.request, 'Permision Granted', button='Ok', timer=3000)

        view_designation = request.POST['view_designation']
        add_designation = request.POST['add_designation']
        change_designation = request.POST['change_designation']
        delete_designation = request.POST['delete_designation']

        content_type = ContentType.objects.get_for_model(Designation, for_concrete_model=False)
        designation_permision = Permission.objects.filter(content_type=content_type)
        for permission in designation_permision:
            if permission.codename == 'view_designation':
                if view_designation == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'add_designation':
                if add_designation == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'change_designation':
                if change_designation == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'delete_designation':
                if delete_designation == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
        sweetify.info(self.request, 'Permision Granted', button='Ok', timer=3000)

        view_goal = request.POST['view_goal']
        add_goal = request.POST['add_goal']
        change_goal = request.POST['change_goal']
        delete_goal = request.POST['delete_goal']

        content_type = ContentType.objects.get_for_model(Goal, for_concrete_model=False)
        goal_permision = Permission.objects.filter(content_type=content_type)
        for permission in goal_permision:
            if permission.codename == 'view_goal':
                if view_goal == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'add_goal':
                if add_goal == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'change_goal':
                if change_goal == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
            if permission.codename == 'delete_goal':
                if delete_goal == 'True':
                    role.permissions.add(permission)
                else:
                    role.permissions.remove(permission)
        sweetify.info(self.request, 'Permision Granted', button='Ok', timer=3000)
        return render(request, 'account/add_roles_permission.html',
                      {'role': role,
                       'view_employee': view_employee,
                       'add_employee': add_employee,
                       'change_employee': change_employee,
                       'delete_employee': delete_employee,

                       'view_department': view_department,
                       'add_department': add_department,
                       'change_department': change_department,
                       'delete_department': delete_department,

                       'view_designation': view_designation,
                       'add_designation': add_designation,
                       'change_designation': change_designation,
                       'delete_designation': delete_designation,

                       'view_goal': view_goal,
                       'add_goal': add_goal,
                       'change_goal': change_goal,
                       'delete_goal': delete_goal,
                       })


def signup(request):
    if request.method == 'POST':
        name = request.POST['name']
        company_name = request.POST['company_name']
        company_phone = request.POST['company_phone']
        company_address = request.POST['company_address']
        email = request.POST['email']
        password = request.POST['password']
        if CompanyStaff.objects.filter(email=email).exists():
            messages.error(request, 'email Already exists')
            return redirect('/signup/')
        else:
            company = Company.objects.create(name=name, company_name=company_name, company_phone=company_phone,
                                             company_address=company_address)
            extend = CompanyStaff(company=company, email=email, password=password)
            extend.password = make_password(extend.password)
            extend.save()
            return HttpResponseRedirect('/')

    return render(request, 'account/signup.html')


class Login(View):
    return_url = None

    def post(self, request):
        email = request.POST['email']
        password = request.POST['password']
        company_staff = CompanyStaff.get_Staff_by_email(email)
        if company_staff is not None:
            if company_staff.is_active:
                if company_staff.is_company_admin:
                    flag = check_password(password, company_staff.password)
                    if flag:
                        company_staff.is_authenticated = True
                        company_staff.save()
                        # request.user = company_staff
                        company_id = company_staff.company.pk
                        # request.session['company'] = company_staff.id
                        request.session['company_staff_id'] = company_staff.id
                        return HttpResponseRedirect(f'/administration/index/{company_id}/{company_staff.pk}')
                    else:
                        return HttpResponseRedirect(settings.LOGIN_URL)

                elif company_staff.is_manager:
                    flag = check_password(password, company_staff.password)
                    if flag:
                        company_staff.is_authenticated = True
                        company_staff.save()
                        # request.user = company_staff
                        company_id = company_staff.company.pk
                        request.session['company_staff_id'] = company_staff.id
                        return HttpResponseRedirect(f"managers/dashboard/{company_id}/{company_staff.pk}")
                    else:
                        return HttpResponseRedirect(settings.LOGIN_URL)

                elif company_staff.is_employee:
                    flag = check_password(password, company_staff.password)
                    if flag:
                        company_staff.is_authenticated = True
                        company_staff.save()
                        # request.user = company_staff
                        company_id = company_staff.company.pk
                        request.session['company_staff_id'] = company_staff.id
                        return HttpResponseRedirect(f"employee/employee_dashboard/{company_id}/{company_staff.pk}")
                    else:
                        return HttpResponseRedirect(settings.LOGIN_URL)

                else:
                    return HttpResponseRedirect(settings.LOGIN_URL)
            else:
                return HttpResponseRedirect(settings.LOGIN_URL)
        else:
            return HttpResponseRedirect(settings.LOGIN_URL)

    def get(self, request):
        return render(request, "account/login.html")


def forgotpass(request):
    context = {}
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = get_object_or_404(CompanyStaff, email=email)
        user.password = make_password(password)
        user.save()
        return HttpResponseRedirect('/')

    return render(request, "account/forgot_pass.html", context)


def reset_password(request):
    email = request.GET["email"]
    try:
        user = get_object_or_404(CompanyStaff, email=email)
        otp = random.randint(1000, 9999)
        msz = "Dear {} \n{} is your One Time Password (OTP) \nDo not share it with others \nThanks&Regards \nMyWebsite".format(
            user.email, otp)
        try:
            email = EmailMessage("Account Verification", msz, to=[user.email])
            email.send()
            return JsonResponse({"status": "sent", "email": user.email, "rotp": otp})
        except:
            return JsonResponse({"status": "error", "email": user.email})
    except:
        return JsonResponse({"status": "failed"})

from django.contrib import admin
from django.urls import path,include
from . import views
from django.contrib.auth import views as auth_views


#
# urls
from .views import SignUpView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic.base import RedirectView
from django.conf import settings

urlpatterns = [
    # path('',views.SignInView.as_view(),name='signin'),
    path('', views.Login.as_view(), name='signin'),
    # path('signup/', SignUpView.as_view(), name='signup'),
    path('signup/', views.signup, name='signup'),
    path('logout/',views.LogoutView.as_view(),name='logout'),
    path('role/',views.RegisterRole.as_view(),name='role'),
    path('rolepermission/<str:name>',views.RolePermissionView.as_view(),name='rolepermission'),
    path('RemoveRole/<str:name>',views.RemoveRole.as_view(),name='RemoveRole'),
    path('usertorole/<str:name>',views.UserToRole.as_view(),name='usertorole'),
    path('RemoveUserToRole/<str:name>/<int:id>',views.RemoveUserToRole.as_view(),name='RemoveUserToRole'),
    # path('autocomplete/',views.autocomplete,name='autocomplete'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='account/password_reset_form.html'),name='password_reset'),
    path('password_reset/done/',auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'),name='password_reset_complete'),

    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("favicon.ico")),
    ),


]



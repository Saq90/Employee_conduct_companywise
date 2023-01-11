from django.contrib import admin

# Register your models here.
from .models import Manager,ManagerEntry,ManagerPost,ManagerAttendance,EmployeeNotification


# Register your models here.


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    class Meta:
        model = Manager
        fields = '__all__'


admin.site.register(ManagerAttendance)
admin.site.register(ManagerEntry)
admin.site.register(ManagerPost)
admin.site.register(EmployeeNotification)


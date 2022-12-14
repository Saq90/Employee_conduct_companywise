from django.contrib import admin
from .models import Client,Lead, Task,notification,holiday,MTask,Asign


# Register your models here.
# -------------------------------------Client---------------------------------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    class Meta:
        model = Client
        fields = '__all__'


# -------------------------------------Leads---------------------------------------------------
@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    class Meta:
        model = Lead
        fields = '__all__'
# -------------------------------------/Leads---------------------------------------------------
admin.site.register(Task)
admin.site.register(notification)
admin.site.register(holiday)
admin.site.register(MTask)
admin.site.register(Asign)

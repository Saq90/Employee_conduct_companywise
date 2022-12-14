from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.db import models
from django.conf import settings

from account.models import Company
from employee.models import Employee
from managers.models import Manager

cilent_status = (
    ('Active', 'Active'),
    ('Inactive', 'Inactive')

)


# --------------------------------------------------------Client-----------------------------------------------------------------------
class Client(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=True,null=True,blank=True)
    client_first_name = models.CharField(max_length=100)
    client_last_name = models.CharField(max_length=100)
    client_username = models.CharField(max_length=100, unique=True)
    client_email = models.EmailField(max_length=100)
    client_id = models.CharField(max_length=100)
    client_address = models.CharField(max_length=100)
    technology = models.CharField(max_length=200,null=True,blank=True)
    description = models.CharField(max_length=500,null=True,blank=True)
    client_phone = models.CharField(max_length=100)
    client_status = models.CharField(choices=cilent_status, max_length=20, default='Active')

    def __str__(self):
        return self.client_first_name
    

    def to_json(self):
        client_details_dict = {
            'id': self.id,
            'client_id': self.client_id,
            'client_first_name': self.client_first_name,
            'client_last_name': self.client_last_name,
            'client_email': self.client_email,
            'client_phone': self.client_phone,
            'client_username': self.client_username,
            'client_address': self.client_address,
            'technology': self.technology,
            'description': self.description,
            'client_status': self.client_status,
        }
        return client_details_dict

    @property
    def get_full_name(self):
        fullname = ''
        firstname = self.client_first_name
        lastname = self.client_last_name

        if firstname and lastname is None:
            fullname = firstname + ' ' + lastname
            return fullname
        return

    def get_absolute_url(self,company_id, company_staff_id):
        return redirect(f'/administration/clients_list/{company_id}/{company_staff_id}')


class Lead(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=True)
    lead_name = models.CharField(max_length=100)
    lead_email = models.EmailField()
    lead_phone = models.CharField(max_length=100)
    lead_project = models.CharField(max_length=100)
    lead_assign_staff = models.CharField(max_length=100)
    lead_created = models.CharField(max_length=100)
    lead_source = models.CharField(max_length=200,blank=True)

    def __str__(self):
        return self.lead_name


    def to_json(self):
        lead_details_dict = {
            'id': self.id,
            'lead_name': self.lead_name,
            'lead_email': self.lead_email,
            'lead_phone': self.lead_phone,
            'lead_project': self.lead_project,
            'lead_assign_staff': self.lead_assign_staff,
            'lead_source': self.lead_source,
            'lead_created': self.lead_created,
        }
        return lead_details_dict
                                                                                                                                                                                                                                                                                        

# --------------------------------------------------------/Leads-----------------------------------------------------------------------


class Task(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=True)
    title = models.CharField(max_length=70)
    description = models.TextField(max_length=500, null=True)
    created_date = models.DateField(default=timezone.now, blank=True)

    assigned_to = models.ForeignKey(
        Manager,
        null=True,
        blank=True,
        related_name="task_assigned_to",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("projectlist")

    def to_json(self):
        project_details_dict = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_date': self.created_date,
            'assigned_to': self.assigned_to.manager_email,
        }

        return project_details_dict



class MTask(models.Model):
    user = models.ForeignKey(Manager, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=70,blank=False)
    description = models.TextField(max_length=500, null=True,blank=False)
    created_date = models.DateField(default=timezone.now, blank=True)

    assigned_to = models.ForeignKey(
        Employee,
        null=True,
        blank=False,
        related_name="task_assigned",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("mtask-detail", kwargs={"pk": self.pk})


class notification(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=True)
    notify = models.CharField(max_length=500,blank=False)


class holiday(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=True)
    day = models.CharField(max_length=40,blank=False)
    date = models.CharField(max_length=40,blank=False)
    occassion = models.CharField(max_length=40,blank=False)
    holidaytype = models.CharField(max_length=40,blank=False)
    status = models.CharField(max_length=40)


class Asign(models.Model):
    employee = models.ForeignKey(Employee,on_delete=models.CASCADE,null=True,blank=False)
    description = models.TextField(max_length=500, null=True,blank=False)
    created_date = models.DateField(default=timezone.now, blank=True)

    assigned_to = models.ForeignKey(
        Manager,
        null=True,
        blank=False,
        related_name="assigned_too",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse("assign-detail", kwargs={"pk": self.pk})

    def to_json(self):
        assign_details_dict = {
            'id': self.id,
            'employee': self.employee.employee_email,
            'description': self.description,
            'created_date': self.created_date,
            'assigned_to': self.assigned_to.manager_email,
        }

        return assign_details_dict

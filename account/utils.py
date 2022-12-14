from django.shortcuts import redirect
from .models import CompanyStaff

def custom_login_required(
    function=None, login_url=None):
    """
    Decorator to extend login required to also check if a notebook auth is
    desired first (but you could customize this to be another check!)
    """

    print('custom login called')
    def wrap(request, *args, **kwargs):
        company_staff_id = request.session.get('company_staff_id')
        if company_staff_id:
            company_staff = CompanyStaff.objects.get(pk=company_staff_id)
            if company_staff.is_authenticated:
                print('Company Staff successfully authenticated....')
                return function(request, *args, **kwargs)
            else:
                return redirect('/')    
        else:
            return redirect('/')
    return wrap

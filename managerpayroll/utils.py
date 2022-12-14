
from io import BytesIO  # A stream implementation using an in-memory bytes buffer
# It inherits BufferIOBase

from django.http import HttpResponse
from django.template.loader import get_template

# pisa is a html2pdf converter using the ReportLab Toolkit,
# the HTML5lib and pyPdf.

from xhtml2pdf import pisa


# difine render_to_pdf() function

def render_to_pdf(context=dict):
    template = get_template("managerpayroll/pdf_template.html")
    html = template.render(context)
    result = BytesIO()

    # This part will create the pdf.
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
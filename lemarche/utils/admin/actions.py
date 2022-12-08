import re
from datetime import date, datetime

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from xlwt import Workbook, Worksheet, XFStyle

from lemarche.utils.admin.export_excel import ExportAction


def convert_data_date(value):
    return value.strftime("%d/%m/%Y")


def convert_boolean_field(value):
    if value:
        return "Oui"
    return "Non"


def export_as_xls(self, request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied
    opts = self.model._meta
    field_names = self.list_display
    file_name = opts.verbose_name
    wb = Workbook(encoding="utf-8")
    ws: Worksheet = wb.add_sheet(file_name)
    font_style = XFStyle()
    font_style.font.bold = True
    pattern_link = r"<a[^>]*>(.*?)</a>"

    headers = ExportAction.generate_header(self, self.model, field_names)
    row_number = 0
    # write header
    for (index, header_item) in enumerate(headers):
        ws.write(row_number, index, header_item, font_style)
    # write content queryset
    for obj in queryset:
        row_number += 1
        for index, field in enumerate(field_names):
            is_admin_field = hasattr(self, field)
            if is_admin_field:
                value = getattr(self, field)(obj)
            else:
                value = getattr(obj, field)
                if isinstance(value, datetime) or isinstance(value, date):
                    value = convert_data_date(value)
                elif isinstance(value, bool):
                    value = convert_boolean_field(value)
            find_content_link = re.search(pattern_link, str(value))
            # if it's link we just send the content
            if find_content_link:
                value = find_content_link.groups()[0]
            ws.write(row_number, index, str(value), font_style)

    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = f"attachment; filename={file_name}.xls"
    wb.save(response)
    return response


export_as_xls.short_description = "Export excel"

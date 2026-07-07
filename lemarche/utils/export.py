import xlwt

from lemarche.siaes.models import Siae


SIAE_FIELDS_TO_EXPORT = [
    "name",
    "brand",
    "kind",
    "address",
    "post_code",
    "city",
    "Référence client 1",
    "Référence client 2",
    "Référence client 3",
]

SIAE_CONTACT_FIELDS = [
    "contact_first_name",
    "contact_last_name",
    "contact_email",
    "contact_phone",
    "contact_social_website",
]

SIAE_FIELD_LABELS = {
    "brand": "Enseigne",
    "post_code": "Code postal",
}


def get_siae_fields(with_contact_info=False):
    siae_field_list = [] + SIAE_FIELDS_TO_EXPORT
    if with_contact_info:
        siae_field_list += SIAE_CONTACT_FIELDS
    return siae_field_list


def generate_header(siae_field_list):
    header = []
    for field_name in siae_field_list:
        if field_name in SIAE_FIELD_LABELS:
            header.append(SIAE_FIELD_LABELS[field_name])
        else:
            try:
                header.append(Siae._meta.get_field(field_name).verbose_name)
            except:  # noqa
                header.append(field_name)
    return header


def generate_siae_row(siae: Siae, siae_field_list):
    siae_row = []
    client_refs = None
    for field_name in siae_field_list:
        col_value = ""
        if field_name in ["nature", "kind"]:
            col_value = getattr(siae, f"get_{field_name}_display")()
        elif field_name == "contact_phone":
            col_value = siae.contact_phone_display
        elif field_name in ["Référence client 1", "Référence client 2", "Référence client 3"]:
            if client_refs is None:
                # rely on the prefetched (and ordered) client_references to avoid an extra query per Siae
                client_refs = list(siae.client_references.all())[:3]
            index = int(field_name[-1]) - 1
            col_value = client_refs[index].name if index < len(client_refs) else ""
        else:
            col_value = getattr(siae, field_name, "")
        siae_row.append(col_value)
    return siae_row


def export_siae_to_csv(csv_writer, siae_queryset, with_contact_info=False):
    # columns
    field_list = get_siae_fields(with_contact_info)

    # header
    csv_writer.writerow(generate_header(field_list))

    # rows
    for siae in siae_queryset:
        siae_row = generate_siae_row(siae, field_list)
        csv_writer.writerow(siae_row)

    return csv_writer


def export_siae_to_excel(siae_queryset, with_contact_info=False):
    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("Structures")

    row_number = 0

    # columns
    field_list = get_siae_fields(with_contact_info)

    # header
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    for index, header_item in enumerate(generate_header(field_list)):
        ws.write(row_number, index, header_item, font_style)

    # rows
    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    for siae in siae_queryset:
        row_number += 1
        siae_row = generate_siae_row(siae, field_list)
        for index, row_item in enumerate(siae_row):
            ws.write(row_number, index, row_item, font_style)

    return wb

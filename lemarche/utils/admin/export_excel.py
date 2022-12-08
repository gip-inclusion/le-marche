class ExportExcelAction:
    @classmethod
    def generate_header(cls, admin, model, list_display):
        def default_format(value):
            return value.replace("_", " ").upper()

        header = []
        for field_display in list_display:
            is_model_field = field_display in [f.name for f in model._meta.fields]
            is_admin_field = hasattr(admin, field_display)
            if is_model_field:
                field = model._meta.get_field(field_display)
                field_name = getattr(field, "verbose_name", field_display)
                header.append(default_format(field_name))
            elif is_admin_field:
                field = getattr(admin, field_display)
                field_name = getattr(field, "short_description", default_format(field_display))
                header.append(default_format(field_name))
            else:
                header.append(default_format(field_display))
        return header

import json

from django import forms


class CustomSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = "includes/_widget_custom_multiselect.html"

    def get_context(self, name, value, attrs):
        if attrs is None:
            attrs = {}
        if "id" not in attrs:
            attrs["id"] = f"id_{name}"

        context = super().get_context(name, value, attrs)

        # Sérialiser les groupes et les options
        groups = []
        options = []

        for group_name, group_options, group_index in context["widget"]["optgroups"]:
            if group_name:
                group = {"name": str(group_name), "options": []}
                for option in group_options:
                    _value = option["value"] if not hasattr(option["value"], "value") else option["value"].value
                    group["options"].append(
                        {
                            "id": f"{attrs['id']}_{_value}",
                            "label": str(option["label"]),
                            "value": _value,
                        }
                    )
                groups.append(group)
            else:
                for option in group_options:
                    _value = option["value"] if not hasattr(option["value"], "value") else option["value"].value
                    options.append(
                        {
                            "id": f"{attrs['id']}_{_value}",
                            "label": str(option["label"]),
                            "value": _value,
                        }
                    )

        context["widget"]["groups_json"] = json.dumps(groups)
        context["widget"]["options_json"] = json.dumps(options)
        context["widget"]["value_json"] = json.dumps(value)
        context["widget"]["value"] = value
        return context

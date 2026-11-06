import openpyxl
from django.test import SimpleTestCase

from lemarche.utils.export import neutralize_csv_formula, set_xlsx_cell_value


class SpreadsheetFormulaNeutralizationTest(SimpleTestCase):
    def test_neutralize_csv_formula(self):
        for value in ["=1+1", "+cmd|calc", "-2+3", "@SUM(A1)", "\t=1+1", "\r=1+1", "\n=1+1"]:
            with self.subTest(value=value):
                self.assertEqual(neutralize_csv_formula(value), f"'{value}")

    def test_neutralize_csv_formula_keeps_safe_values(self):
        for value in ["Raison sociale", "a=b", "", None, 42, -1]:
            with self.subTest(value=value):
                self.assertEqual(neutralize_csv_formula(value), value)

    def test_set_xlsx_cell_value_stores_formula_like_strings_as_text(self):
        cell = openpyxl.Workbook().active.cell(row=1, column=1)

        set_xlsx_cell_value(cell, "=1+1")

        self.assertEqual(cell.value, "=1+1")
        self.assertEqual(cell.data_type, "s")

    def test_set_xlsx_cell_value_keeps_numbers(self):
        cell = openpyxl.Workbook().active.cell(row=1, column=1)

        set_xlsx_cell_value(cell, 42)

        self.assertEqual(cell.value, 42)
        self.assertEqual(cell.data_type, "n")

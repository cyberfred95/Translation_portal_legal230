import csv
import io
import os.path
from typing import Optional

import openpyxl
from rest_framework import serializers


class GlossaryProcessor:

    @staticmethod
    def _validate_csv_file(glossary_file):
        text_file = io.TextIOWrapper(glossary_file, encoding='utf-8')
        csv_reader = csv.reader(text_file)

        for row_number, row in enumerate(csv_reader, start=2):
            if len(row) < 2 or (len(row) == 3 and row[2] != '') or len(row) > 3:
                raise serializers.ValidationError({
                    "detail": f"Invalid row at line {row_number}: {row}. "
                              f"Expected two columns."
                })

        text_file.detach()

    @staticmethod
    def _validate_xlsx_file(glossary_file):
        workbook = openpyxl.load_workbook(glossary_file, data_only=True)
        sheet = workbook.active

        for row_number, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if len(row) < 2 or (len(row) == 3 and row[2]) or len(row) > 3:
                raise serializers.ValidationError({
                    "detail": f"Invalid row at line {row_number}: {row}. "
                              f"Expected two columns."
                })

    def validate_file(self, glossary_file):
        file_extension = os.path.splitext(glossary_file.name)[1]
        if file_extension == '.csv':
            self._validate_csv_file(glossary_file)
        elif file_extension in ['.xlsx', '.xls']:
            self._validate_xlsx_file(glossary_file)
        else:
            raise serializers.ValidationError({"detail": "Invalid file type"})

    def _form_glossary_from_csv(self, glossary_file):
        value = []
        with glossary_file.open(mode='r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader, None)  # Skip header

            for row in csv_reader:
                value.append(f"{row[0]}={row[1]}")

            return {
                "file_name": glossary_file.name,
                "value": value,
                "adaptive": True,
            }

    def _form_glossary_from_xlsx(self, glossary_file) -> dict:
        value = []
        with glossary_file.open(mode='rb') as file:
            workbook = openpyxl.load_workbook(file, data_only=True)
            sheet = workbook.active

            for row in sheet.iter_rows(min_row=2, values_only=True):
                if row[0] is not None and row[1] is not None:
                    value.append(f"{row[0]}={row[1]}")

        return {
            "file_name": glossary_file.name,
            "value": value,
            "adaptive": True,
        }

    def form_glossary_object(self, glossary_file):
        self.validate_file(glossary_file)
        file_extension = os.path.splitext(glossary_file.name)[1]
        if file_extension == '.csv':
            return self._form_glossary_from_csv(glossary_file=glossary_file)

        elif file_extension in ['.xlsx', '.xls']:
            return self._form_glossary_from_xlsx(glossary_file=glossary_file)

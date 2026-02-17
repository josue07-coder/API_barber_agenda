import csv
import io
from typing import List, Dict
from openpyxl import Workbook

def export_to_csv(data: List[Dict]) -> io.StringIO:
        output = io.StringIO()

        if not data:
                return output
        
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        output.seek(0)
        return output

def export_to_excel(data: List[Dict]) -> io.BytesIO:
        output = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"

        if data:
            ws.append(list(data[0].keys()))
        for row in data:
            ws.append(list(row.values()))

        wb.save(output)
        output.seek(0)
        return output
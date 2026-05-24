import csv
import io
from typing import List, Dict, Optional
from openpyxl import Workbook

def export_to_csv(data: List[Dict], fieldnames: Optional[List[str]] = None) -> io.StringIO:
        output = io.StringIO()

        if not data and not fieldnames:
                return output
        
        writer = csv.DictWriter(output, fieldnames=fieldnames or data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        output.seek(0)
        return output

def export_to_excel(data: List[Dict], fieldnames: Optional[List[str]] = None) -> io.BytesIO:
        output = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"

        headers = fieldnames or (list(data[0].keys()) if data else None)
        if headers:
            ws.append(list(headers))
        for row in data:
            ws.append([row.get(field) for field in headers])

        wb.save(output)
        output.seek(0)
        return output

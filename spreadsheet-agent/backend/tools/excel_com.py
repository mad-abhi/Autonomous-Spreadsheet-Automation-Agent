import os
import win32com.client as win32

# Standard Excel COM constants for portability
XL_CENTER = -4108
XL_CONTINUOUS = 1
XL_EDGE_LEFT = 7
XL_EDGE_TOP = 8
XL_EDGE_BOTTOM = 9
XL_EDGE_RIGHT = 10
XL_INSIDE_HORIZONTAL = 12

def create_and_style_excel(filepath: str, data: list[dict]) -> str:
    """
    Creates a formatted Excel workbook at `filepath` using local Excel COM.
    
    Args:
        filepath: Target save path (.xlsx)
        data: List of dictionaries representing row records
    
    Returns:
        Absolute path to the created workbook.
    """
    abs_path = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    # Initialize Excel application
    excel = win32.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        wb = excel.Workbooks.Add()
        ws = wb.ActiveSheet

        if not data:
            wb.SaveAs(abs_path)
            wb.Close(True)
            return abs_path

        headers = list(data[0].keys())

        # 1. Write and Style Headers
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.Cells(1, col_idx)
            cell.Value = str(header).replace("_", " ").title()
            cell.Font.Name = "Segoe UI"
            cell.Font.Size = 11
            cell.Font.Bold = True
            cell.Font.Color = 0xFFFFFF        # White text
            cell.Interior.Color = 0x663300    # Deep Navy Blue (BGR format)
            cell.HorizontalAlignment = XL_CENTER

        # 2. Write Data Rows with Conditional & Zebra Formatting
        for row_idx, record in enumerate(data, start=2):
            for col_idx, header in enumerate(headers, start=1):
                cell = ws.Cells(row_idx, col_idx)
                val = record.get(header, "")
                cell.Value = val
                cell.Font.Name = "Segoe UI"
                cell.Font.Size = 10

                # Currency formatting heuristic
                header_lower = str(header).lower()
                is_currency = any(k in header_lower for k in ["salary", "price", "cost", "revenue", "budget", "amount"])
                if is_currency and isinstance(val, (int, float)):
                    cell.NumberFormat = "$#,##0.00"

                # Alternating row background (Zebra Striping)
                if row_idx % 2 == 0:
                    cell.Interior.Color = 0xF7F7F7

        # 3. Apply Borders to Used Area
        used_range = ws.UsedRange
        for border_id in [XL_EDGE_LEFT, XL_EDGE_RIGHT, XL_EDGE_TOP, XL_EDGE_BOTTOM, XL_INSIDE_HORIZONTAL]:
            border = used_range.Borders(border_id)
            border.LineStyle = XL_CONTINUOUS
            border.Color = 0xD3D3D3

        # 4. Auto-fit column widths with slight padding
        used_range.Columns.AutoFit()
        for col in range(1, len(headers) + 1):
            ws.Columns(col).ColumnWidth = ws.Columns(col).ColumnWidth + 3

        # Save and close
        wb.SaveAs(abs_path)
        wb.Close(True)
        return abs_path

    finally:
        excel.Quit()
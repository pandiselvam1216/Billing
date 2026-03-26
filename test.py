import win32print

report_data = {
    "report_date": "30/03/25",
    "current_date": "30/03/25",
    "current_time": "01:44",
    "list": [
        {"bill_no": 10, "items": 51.0, "tax": "0.00", "discount": "0.00", "amount": 26022.0},
        {"bill_no": 11, "items": 31.0, "tax": "0.00", "discount": "0.00", "amount": 15242.0},
        {"bill_no": 12, "items": 31.0, "tax": "0.00", "discount": "0.00", "amount": 15242.0},
        {"bill_no": 13, "items": 31.0, "tax": "0.00", "discount": "0.00", "amount": 15242.0},
        {"bill_no": 14, "items": 31.0, "tax": "0.00", "discount": "0.00", "amount": 15242.0},
        {"bill_no": 15, "items": 31.0, "tax": "0.00", "discount": "0.00", "amount": 15242.0},
        {"bill_no": 16, "items": 31.0, "tax": "0.00", "discount": "0.00", "amount": 15242.0}
    ],
    "total": {
        "items": 237.0,
        "amount": 117474.0,
        "tax": "0.00",
        "discount": "0.00"
    }
}

# ESC/POS Commands
ESC = b'\x1B'
LF = b'\x0A'
CENTER = ESC + b'\x61\x01'
LEFT = ESC + b'\x61\x00'
RIGHT = ESC + b'\x61\x02'

BOLD_ON = ESC + b'\x45\x01'
BOLD_OFF = ESC + b'\x45\x00'
DOUBLE_WIDTH_ON = ESC + b'\x21\x20'
DOUBLE_WIDTH_OFF = ESC + b'\x21\x00'
DOUBLE_SIZE_ON = ESC + b'\x21\x30'
DOUBLE_SIZE_OFF = ESC + b'\x21\x00'
CUT = LF + LF + LF + LF + LF + b'\x1D\x56\x00'

# Printer Setup
printer_name = win32print.GetDefaultPrinter()
hprinter = win32print.OpenPrinter(printer_name)
hprinter_dc = win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
win32print.StartPagePrinter(hprinter)

# Print Header
win32print.WritePrinter(hprinter, LF)
win32print.WritePrinter(hprinter, CENTER + DOUBLE_SIZE_ON + b"PAKEEZA COLLECTION" + DOUBLE_SIZE_OFF + LF)
win32print.WritePrinter(hprinter, b"No.253 SEPPING ROAD" + LF)
win32print.WritePrinter(hprinter, b"SHIVAJINAGAR BANGALORE 560001" + LF)
win32print.WritePrinter(hprinter, LF)
win32print.WritePrinter(hprinter, BOLD_ON + b"BILLWISE REPORT" + BOLD_OFF + LF)
win32print.WritePrinter(hprinter, LF)
win32print.WritePrinter(hprinter, LEFT + f"PRESENT DATE:{report_data['current_date']}".encode() + b' ' * 17 + f"TIME:{report_data['current_time']}".encode() + LF)
win32print.WritePrinter(hprinter, f"REPORT DATE :{report_data['report_date']}".encode() + LF)

win32print.WritePrinter(hprinter, b'-' * 48 + LF)

# Print Table Header
win32print.WritePrinter(hprinter, BOLD_ON + b"BLNO       ITEMS    TAX    DISC          AMOUNT" + BOLD_OFF + LF)
win32print.WritePrinter(hprinter, b'-' * 48 + LF)

# Print Table Items
# win32print.WritePrinter(hprinter, LEFT)
for item in report_data['list']:
    bill_no, items, tax, discount, amount = item['bill_no'], item['items'], item['tax'], item['discount'], item['amount']
    # Format item line to match PDF spacing
    item_line = f"{bill_no:<6}   {items:>8.2f}   {tax}   {discount}    {amount:>12.2f}"
    win32print.WritePrinter(hprinter, item_line.encode() + LF)
win32print.WritePrinter(hprinter, LEFT + b'-' * 48 + LF)

# # Print Total
item_line = f"TOTAL:{report_data['total']['items']:>11.2f}   0.00   0.00{report_data['total']['amount']:>16.2f}"
win32print.WritePrinter(hprinter, item_line.encode() + LF)

win32print.WritePrinter(hprinter, b'-' * 48 + LF)

# Print Footer Notes
win32print.WritePrinter(hprinter, b"NOTE: TAX AMOUNT INCLUDES OTHER CHARGES" + LF)
win32print.WritePrinter(hprinter, b"NOTE: -VE VALUES INDICATE RETURN BILL" + LF)

# Cut Paper
win32print.WritePrinter(hprinter, CUT)

# End Printing
win32print.EndPagePrinter(hprinter)
win32print.EndDocPrinter(hprinter)
win32print.ClosePrinter(hprinter)

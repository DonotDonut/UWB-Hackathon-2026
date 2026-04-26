from django.shortcuts import render, redirect
from openpyxl import Workbook, load_workbook
from pathlib import Path
import pandas as pd
from django.http import JsonResponse
import sys


BASE_DIR = Path(__file__).resolve().parents[3]
EXCEL_FILE = BASE_DIR / "data" / "staff_data.xlsx"

def dashboard(request):
    return render(request, "dashboard.html")

def add_person(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        role = request.POST.get("role")

        if EXCEL_FILE.exists():
            workbook = load_workbook(EXCEL_FILE)
            sheet = workbook.active
        else:
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Staff"
            sheet.append(["Full Name", "Email", "Role"])

        sheet.append([full_name, email, role])
        workbook.save(EXCEL_FILE)

        return redirect("add_person")

    return render(request, "add_person.html")

def schedules(request):
    df = pd.read_excel(EXCEL_FILE, sheet_name="Shifts")

    # Clean column names
    df.columns = df.columns.str.strip()

    staff_schedule = []
    week_schedule = []

    # Build staff_schedule
    for employee, group in df.groupby("Employee"):
        days = ", ".join(group["Day"].astype(str).tolist())

        times = group.apply(
            lambda row: f"{row['Start Time']} - {row['End Time']}",
            axis=1
        ).unique()

        staff_schedule.append({
            "employee": employee,
            "days": days,
            "time": ", ".join(times),
        })

    # Build week_schedule
    days_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    for day in days_order:
        day_rows = df[df["Day"].astype(str).str.lower() == day.lower()]

        shifts = []

        for _, row in day_rows.iterrows():
            employee = str(row["Employee"])

            shifts.append({
                "employee": employee,
                "time": f"{row['Start Time']} - {row['End Time']}",
                "color": employee.split()[0].lower(),
            })

        week_schedule.append({
            "day": day,
            "shifts": shifts,
        })

    return render(
        request,
        "schedules.html",
        {
            "staff_schedule": staff_schedule,
            "week_schedule": week_schedule,
        },
    )

def edit_shift(request):
    employees = []
    shifts = []

    workbook = load_workbook(EXCEL_FILE)

    staff_sheet = workbook["Staff"]

    if "Shifts" not in workbook.sheetnames:
        shifts_sheet = workbook.create_sheet("Shifts")
        shifts_sheet.append(["Employee", "Day", "Start Time", "End Time"])
        workbook.save(EXCEL_FILE)
    else:
        shifts_sheet = workbook["Shifts"]

    # Load employees
    for row in staff_sheet.iter_rows(min_row=2, values_only=True):
        if row[0]:
            employees.append(row[0])

    # Add shift
    if request.method == "POST" and request.POST.get("action") == "add":
        employee_name = request.POST.get("employee")
        days = request.POST.getlist("days")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        for day in days:
            shifts_sheet.append([employee_name, day, start_time, end_time])

        workbook.save(EXCEL_FILE)
        return redirect("edit_shift")

    # Delete shift
    if request.method == "POST" and request.POST.get("action") == "delete":
        row_number = int(request.POST.get("row_number"))
        shifts_sheet.delete_rows(row_number)
        workbook.save(EXCEL_FILE)
        return redirect("edit_shift")

    # Load existing shifts
    for index, row in enumerate(shifts_sheet.iter_rows(min_row=2, values_only=True), start=2):
        if row[0]:
            shifts.append({
                "row_number": index,
                "employee": row[0],
                "day": row[1],
                "start_time": row[2],
                "end_time": row[3],
            })

    return render(
        request,
        "edit_shift.html",
        {
            "employees": employees,
            "shifts": shifts,
        }
    )
    
    
    



SRC_DIR = Path(__file__).resolve().parents[2]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

print("SRC_DIR:", SRC_DIR)

from backend.main import run_eclat_model

def create_suggested_schedule(request):
    if request.method == "POST":
        result = run_eclat_model()

        return JsonResponse({
            "status": "success",
            "data": result,
        })

    return JsonResponse({"status": "error", "message": "POST required"}, status=405)
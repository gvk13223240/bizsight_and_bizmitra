from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO, StringIO
import csv
import json
import logging
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

from accounts.utils import get_current_business
from analytics_engine.services.sales_metrics import (
    get_sales_overview,
    get_sales_by_day,
    get_sales_by_month,
)
from analytics_engine.services.item_metrics import get_top_items
from analytics_engine.services.smart_insights import get_smart_insights
from insights.services import get_bizmitra_insights

# from billing.utils import send_invoice_email
from .invoice_pdf import generate_invoice_pdf
from .utils import generate_upi_qr
from .models import Bill, BillItem, Payment


def analytics_dashboard_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("/accounts/login/")

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    group = request.GET.get("group", "day")

    bills = Bill.objects.filter(
        business=business,
        is_deleted=False
    )

    if from_date and from_date.lower() != "none":
        try:
            parsed_from = datetime.strptime(from_date, "%Y-%m-%d").date()
            bills = bills.filter(created_at__date__gte=parsed_from)
        except ValueError:
            pass

    if to_date and to_date.lower() != "none":
        try:
            parsed_to = datetime.strptime(to_date, "%Y-%m-%d").date()
            bills = bills.filter(created_at__date__lte=parsed_to)
        except ValueError:
            pass

    overview = get_sales_overview(bills)

    sales_trend = (
        get_sales_by_month(bills)
        if group == "month"
        else get_sales_by_day(bills)
    )

    context = {
        "overview": overview,
        "top_items": get_top_items(bills),
        "insights": get_smart_insights(bills),
        "chart_labels": [str(r["label"]) for r in sales_trend],
        "chart_values": [float(r["total"]) for r in sales_trend],
        "from_date": from_date if from_date and from_date.lower() != "none" else "",
        "to_date": to_date if to_date and to_date.lower() != "none" else "",
        "group": group,
    }

    return render(request, "billing/analytics.html", context)



def dashboard_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("/accounts/login/")

    today = date.today()

    bills = Bill.objects.filter(
        business=business,
        is_deleted=False
    )

    bills_today = bills.filter(created_at__date=today)

    metrics = {
        "today_sales": bills_today.filter(
            payment_status="PAID"
        ).aggregate(total=Sum("total_amount"))["total"] or 0,
        "total_bills": bills.count(),
        "paid": bills.filter(payment_status="PAID").count(),
        "unpaid": bills.filter(payment_status="UNPAID").count(),
        "pay_later": bills.filter(payment_status="PAY_LATER").count(),
    }

    context = {
        "today": timezone.now().strftime("%A, %d %B %Y"),
        "metrics": metrics,
        "recent_bills": bills.order_by("-created_at")[:5],
    }

    return render(request, "billing/dashboard.html", context)



@login_required
def create_bill_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")


    if request.method == "POST":
        item_names = request.POST.getlist("item_name[]")
        quantities = request.POST.getlist("quantity[]")
        prices = request.POST.getlist("price[]")

        subtotal = Decimal("0.00")
        items = []

        for n, q, p in zip(item_names, quantities, prices):
            if not n:
                continue
            try:
                q = int(q)
                p = Decimal(p)
            except Exception:
                continue

            t = q * p
            subtotal += t
            items.append((n, q, p, t))

        if not items:
            messages.error(request, "Add at least one valid item")
            return redirect("create_bill")

        discount = Decimal(request.POST.get("discount") or 0)
        total_amount = max(subtotal - discount, Decimal("0.00"))

        customer_email = request.POST.get("customer_email")

        if total_amount >= 5000 and not customer_email:
            messages.error(
                request,
                "Customer email is required for bills above ₹5,000"
            )
            return redirect("create_bill")

        payment_status = request.POST.get("payment_status")
        payment_mode = request.POST.get("payment_mode")

        bill = Bill.objects.create(
            business=business,
            customer_name=request.POST.get("customer_name"),
            customer_phone=request.POST.get("customer_phone"),
            customer_email=customer_email,
            customer_address=request.POST.get("customer_address"),
            subtotal=subtotal,
            discount=discount,
            total_amount=total_amount,
            payment_status=payment_status,
            email_required=(total_amount >= 5000),
        )

        for n, q, p, t in items:
            BillItem.objects.create(
                bill=bill,
                item_name=n,
                quantity=q,
                price=p,
                total=t,
            )

        if payment_status == "PAID":
            Payment.objects.create(
                bill=bill,
                method=payment_mode,
                reference_id=None
            )

        # if bill.email_required:
        #     pdf_path = generate_invoice_pdf(bill, business)
        #     send_invoice_email(bill, pdf_path)
        #     bill.email_sent = True
        #     bill.save(update_fields=["email_sent"])

        messages.success(request, "Bill created successfully")

        if payment_status == "PAID" and payment_mode == "UPI":
            return redirect("bill_detail", bill.id)
        else:
            return redirect("create_bill")

    return render(request, "billing/create_bill.html")

def bill_detail_view(request, bill_id):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")

    bill = get_object_or_404(
        Bill,
        id=bill_id,
        business=business,
        is_deleted=False
    )

    qr_url = None
    qr_error = None

    if bill.payment_status != "paid":
        if business.upi_id:
            qr_path = generate_upi_qr(
                bill.get_upi_payment_uri(
                    upi_id=business.upi_id,
                    payee_name=business.name
                ),
                bill.bill_number
            )
            qr_url = settings.MEDIA_URL + qr_path.split("media/")[-1]
        else:
            qr_error = "UPI not configured. Please add UPI ID in Business Settings."


    context = {
        "bill": bill,
        "business": business,
        "qr_url": qr_url,   # will be None if paid
        "bizmitra_insights": get_bizmitra_insights(business),
    }

    return render(request, "billing/bill_detail.html", context)



@login_required
def bills_list_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")

    bills = Bill.objects.filter(business=business, is_deleted=False)

    status = request.GET.get("status")
    mode = request.GET.get("mode")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    customer = request.GET.get("customer")

    if status and status != "ALL":
        bills = bills.filter(payment_status=status)

    if mode and mode != "ALL":
        bills = bills.filter(payment__method=mode)

    if from_date:
        bills = bills.filter(created_at__date__gte=from_date)
    if to_date:
        bills = bills.filter(created_at__date__lte=to_date)

    if customer:
        bills = bills.filter(customer_name__icontains=customer)

    context = {
        "bills": bills,
        "status": status,
        "mode": mode,
        "from_date": from_date,
        "to_date": to_date,
        "customer": customer,
    }
    return render(request, "billing/bills_list.html", context)


def download_bill_pdf(request, bill_id):
    bill = get_object_or_404(
        Bill,
        id=bill_id,
        is_deleted=False
    )

    pdf_path = generate_invoice_pdf(bill, bill.business)
    return FileResponse(open(pdf_path, "rb"), as_attachment=True)



def mark_bill_paid(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    bill.payment_status = "PAID"
    bill.save()
    return redirect("bill_detail", bill_id=bill.id)


def filter_bills_by_date(request, queryset):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if from_date:
        queryset = queryset.filter(created_at__date__gte=from_date)

    if to_date:
        queryset = queryset.filter(created_at__date__lte=to_date)

    return queryset


def extract_sheet_csv_url(sheet_url: str) -> str:
    if "export?format=csv" in sheet_url:
        return sheet_url
    try:
        sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    except Exception:
        return sheet_url

def import_google_sheet_view(request):
    if request.method != "POST":
        return redirect("analytics")
    business = get_current_business(request)
    if not business:
        messages.error(request, "Please login to continue")
        return redirect("onboarding")


    sheet_url = request.POST.get("sheet_url")
    if not sheet_url:
        messages.error(request, "No sheet URL provided")
        return redirect("analytics")

    try:
        csv_url = extract_sheet_csv_url(sheet_url)
        response = requests.get(csv_url)
        response.raise_for_status()
    except Exception as e:
        messages.error(request, f"Invalid or private Google Sheet: {e}")
        return redirect("analytics")

    reader = csv.DictReader(StringIO(response.text))


    reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]


    bills_created, errors = 0, []

    for idx, row in enumerate(reader, start=1):
        try:
            qty = int(row["quantity"])
            price = float(row["price"])
            discount = float(row.get("discount", 0))
            total = (qty * price) - discount

            bill = Bill.objects.create(
                business=business,
                customer_name=row.get("customer_name") or "Imported (Google Sheet)",
                customer_phone=row.get("customer_phone"),
                customer_email=row.get("customer_email"),
                subtotal=qty * price,
                discount=discount,
                total_amount=total,
                payment_status=row.get("payment_status", "Pending"),
                created_at=timezone.now(),
            )

            BillItem.objects.create(
                bill=bill,
                item_name=row["item_name"],
                quantity=qty,
                price=price,
                total=qty * price,
            )

            bills_created += 1

        except Exception as e:
            errors.append(f"Row {idx} failed: {e}")
            continue

    if bills_created > 0:
        messages.success(request, f"Imported {bills_created} rows successfully")
    else:
        messages.error(request, f"No rows imported. Errors: {errors[:3]}...")

    return redirect("analytics")



logger = logging.getLogger(__name__)
@login_required
def import_csv_file_view(request):
    if request.method != "POST":
        return redirect("analytics")
    business = get_current_business(request)
    if not business:
        messages.error(request, "Please login to continue")
        return redirect("onboarding")

    csv_file = request.FILES.get("csv_file")
    if not csv_file:
        messages.error(request, "Please upload a CSV file")
        return redirect("analytics")

    try:
        decoded_file = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
    except Exception as e:
        messages.error(request, f"Invalid CSV format: {e}")
        return redirect("analytics")

    bills_created = 0
    failed_rows = []

    year = timezone.now().year
    business_name = business.name.replace(" ", "").upper()
    sequence = Bill.objects.filter(business=business, created_at__year=year).count()

    for row in reader:
        try:
            qty = int((row.get("quantity") or "0").strip())
            price = float((row.get("price") or "0").strip())
            total = qty * price
            discount = float((row.get("discount") or "0").strip())

            bill_date = None
            if row.get("date"):
                try:
                    naive_date = datetime.strptime(row["date"].strip(), "%Y-%m-%d")
                    bill_date = timezone.make_aware(naive_date, timezone.get_current_timezone())
                except Exception as e:
                    logger.warning(f"Invalid date in row {row}: {e}")
                    bill_date = None

            sequence += 1
            bill_number = f"BS_{year}_{business_name}-{sequence:06d}"

            bill = Bill.objects.create(
                business=business,
                bill_number=bill_number,
                customer_name=(row.get("customer_name") or "Imported").strip(),
                customer_phone=(row.get("customer_phone") or "").strip(),
                customer_email=(row.get("customer_email") or "").strip(),
                subtotal=total,
                discount=discount,
                total_amount=max(total - discount, 0),
                payment_status=(row.get("payment_status") or "UNPAID").strip().upper(),
                created_at=bill_date or timezone.now(),
            )

            BillItem.objects.create(
                bill=bill,
                item_name=(row.get("item_name") or "").strip(),
                quantity=qty,
                price=price,
                total=total,
            )

            if bill.payment_status == "PAID":
                Payment.objects.create(
                    bill=bill,
                    method=(row.get("payment_mode") or "CASH").strip(),
                    reference_id=None
                )

            bills_created += 1

        except Exception as e:
            failed_rows.append({"row": row, "error": str(e)})
            logger.error(f"Row failed: {row} | Error: {e}")
            continue

    if bills_created > 0:
        messages.success(request, f"Imported {bills_created} rows successfully")
    if failed_rows:
        messages.warning(request, f"{len(failed_rows)} rows failed. Check logs for details.")

    return redirect("analytics")



@login_required
def bulk_delete_bills_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")

    if request.method == "POST":
        bill_ids = request.POST.getlist("bill_ids")
        if bill_ids:
            Bill.objects.filter(id__in=bill_ids, business=business).update(is_deleted=True)
            messages.success(request, f"Deleted {len(bill_ids)} bills successfully")
        else:
            messages.warning(request, "No bills selected")

    return redirect("bills_list")


def preview_import_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")

    rows = []
    if request.method == "POST":
        sheet_url = request.POST.get("sheet_url")
        if sheet_url:
            try:
                sheet_id = sheet_url.split("/d/")[1].split("/")[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                response = requests.get(csv_url)
                response.raise_for_status()
                reader = csv.DictReader(StringIO(response.text))
                rows = list(reader)
            except Exception:
                messages.error(request, "Invalid or private Google Sheet")
                return redirect("analytics")

        elif request.FILES.get("csv_file"):
            try:
                decoded_file = request.FILES["csv_file"].read().decode("utf-8").splitlines()
                reader = csv.DictReader(decoded_file)
                rows = list(reader)
            except Exception:
                messages.error(request, "Invalid CSV file")
                return redirect("analytics")

    return render(request, "billing/preview_import.html", {"rows": rows})
import json

def confirm_import_view(request):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")

    if request.method == "POST":
        rows = json.loads(request.POST.get("rows_json", "[]"))
        bills_created = 0

        for row in rows:
            try:
                qty = int(row["quantity"])
                price = float(row["price"])
                total = qty * price

                bill = Bill.objects.create(
                    business=business,
                    customer_name="Imported",
                    subtotal=total,
                    discount=0,
                    total_amount=total,
                    payment_status="PAID",
                )
                BillItem.objects.create(
                    bill=bill,
                    item_name=row["item_name"],
                    quantity=qty,
                    price=price,
                    total=total,
                )
                bills_created += 1
            except Exception:
                continue

        messages.success(request, f"Imported {bills_created} rows successfully")
        return redirect("analytics")


def download_sales_excel(request):
    business = get_current_business(request)
    if not business:
        return redirect("onboarding")

    bills = Bill.objects.filter(business=business)
    bills = filter_bills_by_date(request, bills)

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    ws.append([
        "Bill Number", "Date", "Customer",
        "Subtotal", "Discount", "Total", "Status"
    ])

    for bill in bills:
        ws.append([
            bill.bill_number,
            bill.created_at.strftime("%Y-%m-%d"),
            bill.customer_name or "Walk-in",
            float(bill.subtotal),
            float(bill.discount),
            float(bill.total_amount),
            bill.payment_status,
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="BS_{timezone.now().year}_{business.name}_sales.xlsx"'
    return response

def download_sales_csv(request):
    business = get_current_business(request)
    if not business:
        messages.error(request, "Please login to continue")
        return redirect("onboarding")

    bills = Bill.objects.filter(business=business)
    bills = filter_bills_by_date(request, bills)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="BS_{timezone.now().year}_{business.name}_sales.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Bill Number", "Date", "Customer",
        "Subtotal", "Discount", "Total", "Status"
    ])

    for bill in bills:
        writer.writerow([
            bill.bill_number,
            bill.created_at.strftime("%Y-%m-%d"),
            bill.customer_name or "Walk-in",
            bill.subtotal,
            bill.discount,
            bill.total_amount,
            bill.payment_status,
        ])

    return response

def download_sales_pdf(request):
    business = get_current_business(request)
    if not business:
        messages.error(request, "Please login to continue")
        return redirect("onboarding")

    bills = Bill.objects.filter(business=business)
    bills = filter_bills_by_date(request, bills)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="BS_{timezone.now().year}_{business.name}_sales.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph(
            f"<b>BizSight Sales Report</b><br/>{business.name}",
            styles["Title"],
        )
    )
    elements.append(Spacer(1, 12))

    table_data = [["Bill", "Date", "Customer", "Total", "Status"]]

    for bill in bills:
        table_data.append([
            bill.bill_number,
            bill.created_at.strftime("%d-%m-%Y"),
            bill.customer_name or "Walk-in",
            f"₹{bill.total_amount}",
            bill.payment_status,
        ])

    elements.append(Table(table_data))
    doc.build(elements)

    return response

def delete_bill_view(request, bill_id):
    business = get_current_business(request)

    bill = get_object_or_404(
        Bill,
        id=bill_id,
        business=business,
        is_deleted=False
    )

    bill.is_deleted = True
    bill.deleted_at = timezone.now()
    bill.save(update_fields=["is_deleted", "deleted_at"])

    messages.success(request, "Bill deleted")
    return redirect("bills_list")

from datetime import datetime
import io
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, fields, Subquery, OuterRef
from django.utils.dateparse import parse_date
from apps.complaints.models import Complaint, ComplaintStatusHistory
from apps.users.models import Role
import openpyxl
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def get_filtered_complaints_queryset(profile, filters):
    """
    Returns a Complaint queryset filtered by query parameters and scoped to the user's role.
    - System Admin: Can view all, and can filter by department.
    - Department Admin: Locked to their own department, department filter is ignored.
    """
    queryset = Complaint.objects.all()

    # RBAC Enforcement
    if profile.role_name == Role.DEPARTMENT_ADMIN:
        queryset = queryset.filter(assigned_department_id=profile.department_id)
    elif profile.role_name == Role.SYSTEM_ADMIN:
        department_id = filters.get('department')
        if department_id:
            queryset = queryset.filter(assigned_department_id=department_id)

    # Date filters
    start_date = filters.get('start_date')
    if start_date:
        parsed_start = parse_date(start_date)
        if parsed_start:
            queryset = queryset.filter(submitted_at__date__gte=parsed_start)

    end_date = filters.get('end_date')
    if end_date:
        parsed_end = parse_date(end_date)
        if parsed_end:
            queryset = queryset.filter(submitted_at__date__lte=parsed_end)

    # Category filter
    category_id = filters.get('category')
    if category_id:
        queryset = queryset.filter(category_id=category_id)

    # District filter
    district = filters.get('district')
    if district:
        queryset = queryset.filter(district__iexact=district)

    return queryset


def get_analytics_data(queryset):
    """
    Computes aggregations (counts, averages) for the given Complaint queryset.
    """
    # 1. Overall Statuses
    # pending = submitted, under_verification, assigned, verified, in_progress
    # resolved = resolved, closed
    # invalid = invalid
    status_counts = queryset.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status__in=['submitted', 'under_verification', 'assigned', 'verified', 'in_progress'])),
        resolved=Count('id', filter=Q(status__in=['resolved', 'closed'])),
        invalid=Count('id', filter=Q(status='invalid')),
    )

    # 2. Breakdowns
    category_breakdown = list(queryset.values('category__name').annotate(count=Count('id')).order_by('-count'))
    department_breakdown = list(queryset.values('assigned_department__name').annotate(count=Count('id')).order_by('-count'))
    district_breakdown = list(queryset.values('district').annotate(count=Count('id')).order_by('-count'))
    priority_breakdown = list(queryset.values('priority_category').annotate(count=Count('id')).order_by('-count'))

    # 3. Average Resolution Time
    # Get the timestamp of when it became 'resolved'
    resolution_time_subquery = ComplaintStatusHistory.objects.filter(
        complaint=OuterRef('pk'),
        new_status='resolved'
    ).order_by('-changed_at').values('changed_at')[:1]
    
    resolved_qs = queryset.filter(status__in=['resolved', 'closed']).annotate(
        resolved_at=Subquery(resolution_time_subquery)
    ).exclude(resolved_at__isnull=True)

    # Calculate difference between submitted_at and resolved_at
    avg_resolution = resolved_qs.annotate(
        duration=ExpressionWrapper(F('resolved_at') - F('submitted_at'), output_field=fields.DurationField())
    ).aggregate(avg_time=Avg('duration'))

    avg_time = avg_resolution['avg_time']
    avg_resolution_str = str(avg_time) if avg_time else None

    return {
        'summary': {
            'total': status_counts['total'],
            'pending': status_counts['pending'],
            'resolved': status_counts['resolved'],
            'invalid': status_counts['invalid'],
            'avg_resolution_time': avg_resolution_str
        },
        'breakdowns': {
            'category': [{'name': item['category__name'] or 'Uncategorized', 'count': item['count']} for item in category_breakdown],
            'department': [{'name': item['assigned_department__name'] or 'Unassigned', 'count': item['count']} for item in department_breakdown],
            'district': [{'name': item['district'] or 'Unknown', 'count': item['count']} for item in district_breakdown],
            'priority': [{'name': item['priority_category'] or 'Unassessed', 'count': item['count']} for item in priority_breakdown],
        }
    }


def generate_excel_report(analytics_data, queryset):
    wb = openpyxl.Workbook()
    
    # Sheet 1: Summary
    ws_summary = wb.active
    ws_summary.title = "Summary"
    ws_summary.append(["Report Summary"])
    ws_summary.append(["Total Complaints", analytics_data['summary']['total']])
    ws_summary.append(["Pending", analytics_data['summary']['pending']])
    ws_summary.append(["Resolved/Closed", analytics_data['summary']['resolved']])
    ws_summary.append(["Invalid/Rejected", analytics_data['summary']['invalid']])
    ws_summary.append(["Average Resolution Time", analytics_data['summary']['avg_resolution_time'] or "N/A"])
    
    # Sheet 2: Complaints Data
    ws_data = wb.create_sheet(title="Complaints")
    headers = ["Complaint Number", "Submitted At", "Category", "Department", "District", "Status", "Priority"]
    ws_data.append(headers)
    
    # Fetch data directly for export (avoiding N+1 queries)
    export_qs = queryset.select_related('category', 'assigned_department')
    for complaint in export_qs:
        ws_data.append([
            complaint.complaint_number,
            complaint.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if complaint.submitted_at else '',
            complaint.category.name if complaint.category else '',
            complaint.assigned_department.name if complaint.assigned_department else '',
            complaint.district or '',
            complaint.status,
            complaint.priority_category or ''
        ])
        
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream.read()


def generate_pdf_report(analytics_data, queryset, filters):
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph("Civic Complaints Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Filters
    elements.append(Paragraph("Applied Filters:", styles['Heading3']))
    filter_text = ", ".join([f"{k}: {v}" for k, v in filters.items() if v])
    if not filter_text:
        filter_text = "None"
    elements.append(Paragraph(filter_text, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Summary Table
    elements.append(Paragraph("Summary Statistics", styles['Heading3']))
    summary_data = [
        ["Total Complaints", str(analytics_data['summary']['total'])],
        ["Pending", str(analytics_data['summary']['pending'])],
        ["Resolved/Closed", str(analytics_data['summary']['resolved'])],
        ["Invalid/Rejected", str(analytics_data['summary']['invalid'])],
        ["Avg Resolution Time", str(analytics_data['summary']['avg_resolution_time'] or "N/A")]
    ]
    summary_table = Table(summary_data, colWidths=[200, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))
    
    # Complaints Data Table
    elements.append(Paragraph("Complaint Details", styles['Heading3']))
    data_headers = ["Number", "Date", "Category", "Department", "District", "Status", "Priority"]
    data = [data_headers]
    
    export_qs = queryset.select_related('category', 'assigned_department')[:1000] # Limit to 1000 for PDF to avoid memory issues
    for complaint in export_qs:
        data.append([
            complaint.complaint_number,
            complaint.submitted_at.strftime('%Y-%m-%d') if complaint.submitted_at else '',
            (complaint.category.name if complaint.category else '')[:15],
            (complaint.assigned_department.name if complaint.assigned_department else '')[:15],
            (complaint.district or '')[:15],
            complaint.status,
            complaint.priority_category or ''
        ])
        
    data_table = Table(data, repeatRows=1)
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(data_table)
    
    doc.build(elements)
    stream.seek(0)
    return stream.read()

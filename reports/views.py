
import csv

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status as http
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import services


def _days_or_error(request):
    try:
        return services.parse_days(request.query_params.get('days')), None
    except ValueError as exc:
        return None, Response(
            {'status': 'error', 'message': str(exc)},
            status=http.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def report(request):
    """Full report. GET /api/reports/?days=30"""
    days, err = _days_or_error(request)
    if err:
        return err

    return Response(services.build_report(days))


@api_view(['GET'])
def summary(request):
    days, err = _days_or_error(request)
    if err:
        return err

    data = services.build_report(days)
    return Response({
        'range': data['range'],
        **data['summary']
    })


@api_view(['GET'])
def production_over_time(request):
    days, err = _days_or_error(request)
    if err:
        return err

    data = services.build_report(days)
    return Response({
        'range': data['range'],
        **data['production_over_time']
    })


@api_view(['GET'])
def ingredient_usage(request):
    """GET /api/reports/ingredient-usage/?days=30&status=Low"""
    days, err = _days_or_error(request)
    if err:
        return err

    data = services.build_report(
        days,
        status_filter=request.query_params.get('status')
    )

    return Response({
        'range': data['range'],
        **data['ingredient_usage']
    })


@api_view(['GET'])
def inventory_status(request):
    days, err = _days_or_error(request)
    if err:
        return err

    data = services.build_report(days)
    return Response({
        'range': data['range'],
        **data['inventory_status']
    })


@api_view(['GET'])
def stock_by_category(request):
    days, err = _days_or_error(request)
    if err:
        return err

    data = services.build_report(days)
    return Response({
        'range': data['range'],
        'items': data['stock_by_category']
    })


@api_view(['GET'])
def export_csv(request):
    """CSV download of the same report. GET /api/reports/export/?days=30"""
    days, err = _days_or_error(request)
    if err:
        return err

    data = services.build_report(days)

    stamp = timezone.localtime().strftime('%Y%m%d')

    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = (
        f'attachment; filename="BENZ_Coffee_Report_{stamp}.csv"'
    )

    w = csv.writer(resp)

    w.writerow(['BENZ COFFEE - Reports & Statistics'])
    w.writerow([
        f'Last {days} days',
        data['range']['start_date'],
        data['range']['end_date']
    ])

    w.writerow([])

    w.writerow(['Summary'])
    w.writerow(['Total production', data['summary']['total_production']])
    w.writerow(['Ingredients used', data['summary']['ingredients_used']])
    w.writerow(['Low / out of stock items', data['summary']['low_stock_items']])

    w.writerow([])

    w.writerow(['Inventory Status'])
    w.writerow(['In Stock', data['inventory_status']['in_stock']])
    w.writerow(['Low Stock', data['inventory_status']['low_stock']])
    w.writerow(['Out of Stock', data['inventory_status']['out_of_stock']])
    w.writerow(['Total Ingredients', data['inventory_status']['total']])

    w.writerow([])

    w.writerow(['Production Over Time'])
    w.writerow(['Date', 'Units produced'])

    for row in data['production_over_time']['data']:
        w.writerow([row['date'], row['units']])

    w.writerow([])

    w.writerow(['Ingredients Usage'])
    w.writerow(['Ingredient', 'Used', 'Unit', 'Current stock', 'Status'])

    for row in data['ingredient_usage']['items']:
        w.writerow([
            row['name'],
            row['used'],
            row['unit'],
            row['current_stock'],
            row['status']
        ])

    w.writerow([])

    w.writerow(['Stock Level by Category'])
    w.writerow(['Category', 'Ingredient count'])

    for category in data['stock_by_category']:
        w.writerow([category['category'], category['count']])

    return resp

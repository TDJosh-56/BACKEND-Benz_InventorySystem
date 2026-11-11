from datetime import date, datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog
from .serializers import AuditLogCreateSerializer, AuditLogSerializer

DEFAULT_LIMIT = 1000
MAX_LIMIT = 5000


def _day_start(d):
    return timezone.make_aware(datetime.combine(d, time.min))


def period_range(period, anchor):
    """[start, end) datetimes for Day / Week (Mon-Sun) / Month around `anchor`."""
    if period == 'day':
        start, end = anchor, anchor + timedelta(days=1)
    elif period == 'week':
        start = anchor - timedelta(days=anchor.weekday())
        end = start + timedelta(days=7)
    else:  # month
        start = anchor.replace(day=1)
        end = (start.replace(year=start.year + 1, month=1) if start.month == 12
               else start.replace(month=start.month + 1))
    return _day_start(start), _day_start(end)


def _bad(message):
    return Response({'status': 'error', 'message': message}, status=status.HTTP_400_BAD_REQUEST)


class AuditLogListView(APIView):
    """
    GET  /api/audit-logs/?period=all|day|week|month&date=YYYY-MM-DD
                        &category=inventory|production|recipe|settings
                        &search=text&limit=1000&offset=0
    POST /api/audit-logs/   (record an event the backend did not generate itself)

    There is deliberately no PATCH / DELETE: an audit trail is append-only.
    """

    def get(self, request):
        p = request.query_params
        qs = AuditLog.objects.all()

        category = (p.get('category') or '').strip().lower()
        if category and category != 'all':
            if category not in AuditLog.Category.values:
                return _bad(f'category must be one of: {", ".join(AuditLog.Category.values)}.')
            qs = qs.filter(category=category)

        period = (p.get('period') or 'all').strip().lower()
        if period not in ('all', 'day', 'week', 'month'):
            return _bad('period must be one of: all, day, week, month.')
        if period != 'all':
            try:
                anchor = date.fromisoformat(p['date']) if p.get('date') else timezone.localdate()
            except ValueError:
                return _bad('date must be formatted YYYY-MM-DD.')
            start, end = period_range(period, anchor)
            qs = qs.filter(timestamp__gte=start, timestamp__lt=end)

        search = (p.get('search') or '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(subtitle__icontains=search) |
                Q(category__icontains=search) | Q(change_label__icontains=search))

        try:
            limit = min(max(int(p.get('limit', DEFAULT_LIMIT)), 1), MAX_LIMIT)
            offset = max(int(p.get('offset', 0)), 0)
        except ValueError:
            return _bad('limit and offset must be whole numbers.')

        rows = qs.order_by('-timestamp', '-id')[offset:offset + limit]
        return Response(AuditLogSerializer(rows, many=True).data)

    def post(self, request):
        ser = AuditLogCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        entry = ser.save()
        return Response(AuditLogSerializer(entry).data, status=status.HTTP_201_CREATED)

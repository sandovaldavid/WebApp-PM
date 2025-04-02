from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django.db.utils import OperationalError
from django.conf import settings
import datetime


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    Health check endpoint that verifies:
    1. API is running
    2. Authentication is working (requires valid token)
    3. Database connection is working
    4. Returns basic system information
    """
    # Check database connection
    db_status = "OK"
    db_error = None
    try:
        # Execute simple query to verify DB connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError as e:
        db_status = "ERROR"
        db_error = str(e)

    # Get current application version if available
    try:
        app_version = settings.VERSION
    except AttributeError:
        app_version = "Not defined"

    health_data = {
        "status": "API is operational",
        "timestamp": datetime.datetime.now().isoformat(),
        "user": request.user.nombreusuario,
        "database": db_status,
        "version": app_version,
        "environment": getattr(settings, "ENVIRONMENT", "development"),
    }

    if db_error:
        health_data["database_error"] = db_error
        return Response(health_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(health_data)

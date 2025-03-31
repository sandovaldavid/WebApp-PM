from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from dashboard.models import Usuario
import logging

# Setup logging
logger = logging.getLogger(__name__)


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that supports email-based authentication
    for both API and web application
    """

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        try:
            # Handle either username or email being passed
            lookup_field = email or username

            # Add debug logging
            logger.debug(f"Attempting authentication with lookup_field: {lookup_field}")

            if not lookup_field or not password:
                logger.debug("Missing lookup_field or password")
                return None

            # Try to find a user that matches either email or username
            # Use case-insensitive lookup for email
            user = Usuario.objects.get(
                Q(email__iexact=lookup_field) | Q(nombreusuario__exact=lookup_field)
            )

            logger.debug(f"Found user: {user.nombreusuario}")

            # Check the password
            if user.check_password(password):
                logger.debug("Password check successful")
                return user
            else:
                logger.debug("Password check failed")

        except Usuario.DoesNotExist:
            logger.debug("User does not exist")
            # Run the default password hasher once to reduce timing attacks
            Usuario().set_password(password)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")

        return None

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from api.serializers.usuario_serializers import UsuarioSerializer
from dashboard.models import Usuario
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
import logging
from django.db import transaction, connection

# Setup logging for debugging
logger = logging.getLogger(__name__)


class LoginView(ObtainAuthToken):
    """
    Enhanced login endpoint that returns token and user data
    """

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            logger.warning("API login attempt with missing credentials")
            return Response(
                {"error": "Por favor proporcione email y password"}, status=400
            )

        logger.debug(f"API Login attempt with email: {email}")

        try:
            # First try to get the user by email
            user = Usuario.objects.get(email=email)

            # Check if the account is confirmed
            if not user.confirmado and hasattr(user, "confirmado"):
                logger.warning(f"API login attempt for unconfirmed account: {email}")
                return Response({"error": "La cuenta no está confirmada"}, status=400)

            # Directly check the password
            if check_password(password, user.contrasena):
                logger.info(f"API login successful for: {user.nombreusuario}")

                # Use raw SQL to handle token creation/retrieval
                # This bypasses ORM issues with the token model
                try:
                    with transaction.atomic():
                        # First try to get the existing token
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "DELETE FROM authtoken_token WHERE user_id = %s",
                                [user.pk],
                            )

                        # Generate a new token key
                        import binascii
                        import os

                        token_key = binascii.hexlify(os.urandom(20)).decode()

                        # Insert new token directly
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO authtoken_token (key, user_id, created) VALUES (%s, %s, NOW())",
                                [token_key, user.pk],
                            )
                except Exception as e:
                    logger.error(f"Token creation error: {str(e)}")
                    # Fallback to manual token creation
                    import os

                    token_key = f"manual-token-{user.pk}-{os.urandom(8).hex()}"

                # Create a basic user data dictionary to avoid serializer issues
                user_data = {
                    "idusuario": user.idusuario,
                    "nombreusuario": user.nombreusuario,
                    "email": user.email,
                    "rol": user.rol,
                }

                # Return both token and user data
                return Response({"token": token_key, "user": user_data})
            else:
                logger.warning(f"API login failed - incorrect password for: {email}")
                return Response({"error": "Credenciales inválidas"}, status=400)

        except Usuario.DoesNotExist:
            logger.warning(f"API login failed - user not found: {email}")
            return Response({"error": "Usuario no encontrado"}, status=400)
        except Exception as e:
            logger.error(f"API login error: {str(e)}")
            return Response({"error": "Error durante la autenticación"}, status=500)

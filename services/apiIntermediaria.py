import os
import re
import requests
import logging
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


class APIIntermediaService:
    """
    Service for interacting with the intermediate API
    """

    def __init__(self, api_base_url=None):
        """Initialize the service with an optional custom base URL"""
        # Get base URL from environment variable or use default
        self.api_base_url = api_base_url or os.environ.get(
            "API_INTERMEDIARIA_URL", "http://localhost:3000/api"
        )
        self.token = os.environ.get("API_INTERMEDIARIA_TOKEN")

        # Get timeout from environment variable or use default (30 seconds)
        try:
            self.timeout = int(os.environ.get("API_INTERMEDIARIA_TIMEOUT", 30))
        except (ValueError, TypeError):
            self.timeout = 30

        logger.info(
            f"Initializing API service with URL: {self.api_base_url}, timeout: {self.timeout}s"
        )

    def get_headers(self):
        """Get headers with authorization token if available"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            logger.info(f"Using API token from environment variable")
        else:
            logger.warning("API_INTERMEDIARIA_TOKEN not found in environment variables")

        return headers

    def parameterize_task(self, tarea, api_url=None):
        """
        Connect to external API to parameterize a task with AI assistance.
        Updates the task with parameters like estimated duration, tags, complexity, etc.

        Args:
            tarea: The task object to parameterize
            api_url: Optional custom API URL

        Returns:
            dict: A dictionary containing the response data and update information
        """
        # Configure the API endpoint
        api_base_url = api_url or self.api_base_url
        api_endpoint = f"{api_base_url}/tasks/{tarea.idtarea}/parameterize"

        logger.info(f"Making API request to: {api_endpoint}")

        try:
            # Set up headers with authorization token
            headers = self.get_headers()

            # Log the request attempt
            logger.info(f"Connecting to API with timeout of {self.timeout}s")

            # Make the request to the external API with auth headers
            response = requests.get(api_endpoint, headers=headers, timeout=self.timeout)
            response.raise_for_status()  # Raise exception for non-200 responses

            data = response.json()
            logger.info(f"API response received successfully: {response.status_code}")

            if not data.get("success"):
                logger.error(
                    f"API returned error: {data.get('message', 'Unknown error')}"
                )
                return {
                    "success": False,
                    "error": "API call was unsuccessful",
                    "details": data.get("message", "Unknown error"),
                }

            # Extract data from the response
            task_data = data.get("data", {})
            logger.debug(f"Task data received: {task_data}")

            # Process and update task fields based on the response
            updates = {}

            # Update task name if provided
            if "tarea" in task_data:
                updates["nombretarea"] = task_data["tarea"]

            # Update task type if provided
            if "tipo" in task_data:
                from dashboard.models import TipoTarea

                tipo_nombre = task_data["tipo"]
                # Try to find an existing task type or create a new one
                tipo_tarea, created = TipoTarea.objects.get_or_create(
                    nombre__iexact=tipo_nombre, defaults={"nombre": tipo_nombre}
                )
                updates["tipo_tarea"] = tipo_tarea

            # Update tags if provided
            if "palabras_clave" in task_data and isinstance(
                task_data["palabras_clave"], list
            ):
                # Convert list to comma-separated string
                updates["tags"] = ",".join(task_data["palabras_clave"])

            # Update complexity/difficulty if provided
            if "complejidad" in task_data:
                # Map text values to numeric values
                complexity_map = {
                    "Baja": 1,
                    "Media": 2,
                    "Alta": 3,
                    "Muy Alta": 4,
                    "Extrema": 5,
                }
                difficulty = complexity_map.get(task_data["complejidad"], None)
                if difficulty:
                    updates["dificultad"] = difficulty

            # Update estimated duration if provided
            if "tiempo_estimado" in task_data:
                try:
                    # Extract numeric value from strings like "8 días"
                    tiempo_str = task_data["tiempo_estimado"]
                    # Basic parsing - extract the first number found

                    time_value = re.search(r"\d+", tiempo_str)
                    if time_value:
                        updates["duracionestimada"] = int(time_value.group())
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Could not parse tiempo_estimado: {e}")

            # Update clarity of requirements if provided
            if "claridad_requisitos" in task_data:
                try:
                    # Convert percentage string like "85%" to float 0.85
                    claridad_str = task_data["claridad_requisitos"]
                    claridad_value = float(claridad_str.strip("%")) / 100
                    updates["claridad_requisitos"] = claridad_value
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Could not parse claridad_requisitos: {e}")

            # Update story points / estimated size if provided
            if "puntos_historia" in task_data:
                try:
                    puntos = int(task_data["puntos_historia"])
                    updates["tamaño_estimado"] = puntos
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse puntos_historia: {e}")

            # Update last modification date
            updates["fechamodificacion"] = datetime.now()

            # Apply all updates to the task
            for field, value in updates.items():
                setattr(tarea, field, value)

            tarea.save()
            logger.info(
                f"Task {tarea.idtarea} updated successfully with {len(updates)} fields"
            )

            return {
                "success": True,
                "updated_fields": list(updates.keys()),
                "data": data,
            }

        except requests.exceptions.Timeout:
            logger.error(f"API request timed out after {self.timeout} seconds")
            return {
                "success": False,
                "error": f"API connection timed out after {self.timeout} seconds. The service at {api_base_url} may be down or overloaded.",
                "status_code": 504,  # Gateway Timeout
            }
        except requests.exceptions.ConnectionError:
            logger.error(
                f"API connection failed. Service may be offline: {api_base_url}"
            )
            return {
                "success": False,
                "error": f"Could not connect to the API service at {api_base_url}. Please check that the service is running.",
                "status_code": 503,  # Service Unavailable
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {
                "success": False,
                "error": f"Failed to connect to parameterization API: {str(e)}",
                "status_code": 503,
            }
        except Exception as e:
            logger.error(f"Task parameterization error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error during task parameterization: {str(e)}",
                "status_code": 500,
            }

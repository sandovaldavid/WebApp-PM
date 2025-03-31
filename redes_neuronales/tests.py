from django.test import TestCase, override_settings
from django.core.cache import cache
import multiprocessing
import time
import uuid
import json
from django.db.models.signals import pre_save, post_save, post_delete
from unittest.mock import patch


# Función para escribir en la caché desde un proceso separado
def write_to_cache(cache_key, data):
    """Función que será ejecutada en un proceso independiente para escribir en cache"""
    from django.core.cache import cache

    # Asegurarse de que se está escribiendo en Redis
    print(f"Proceso hijo: Escribiendo en cache con key {cache_key}")
    cache.set(cache_key, data, 60)
    print(f"Proceso hijo: Datos escritos en cache {data}")


# Configuración especial para evitar problemas de auditoría en las pruebas
@override_settings(AUDIT_ENABLED=False)
class RedisTestCase(TestCase):
    """Clase base para pruebas que requieren Redis y evitan la auditoría"""

    @classmethod
    def setUpClass(cls):
        # Desactivar las señales de auditoría globalmente
        cls._disconnect_audit_signals()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Reactivar las señales de auditoría
        cls._reconnect_audit_signals()

    def setUp(self):
        # Crear un parche para que las funciones de auditoría no hagan nada
        self.audit_patches = [
            patch(
                "auditoria.middleware.AuditoriaMiddleware.registrar_actividad_navegacion",
                return_value=None,
            ),
            patch("auditoria.signals.registrar_cambios", return_value=None),
        ]
        # Activar los parches
        for p in self.audit_patches:
            p.start()

        # También configuramos un mock para el contexto de usuario actual
        self.user_patch = patch("auditoria.signals.get_current_user", return_value=None)
        self.user_patch.start()

    def tearDown(self):
        # Desactivar los parches
        for p in self.audit_patches:
            p.stop()
        self.user_patch.stop()

    @classmethod
    def _disconnect_audit_signals(cls):
        """Desconecta las señales de auditoría para evitar errores durante las pruebas"""
        try:
            from auditoria.signals import (
                audit_post_save,
                audit_post_delete,
                pre_save_handler,
            )

            pre_save.disconnect(pre_save_handler, dispatch_uid="pre_save_audit")
            post_save.disconnect(audit_post_save, dispatch_uid="post_save_audit")
            post_delete.disconnect(audit_post_delete, dispatch_uid="post_delete_audit")
            print("✓ Señales de auditoría desconectadas correctamente")
        except (ImportError, ValueError, KeyError) as e:
            print(f"! No se pudieron desconectar algunas señales de auditoría: {e}")

    @classmethod
    def _reconnect_audit_signals(cls):
        """Reconecta las señales de auditoría al terminar las pruebas"""
        try:
            from auditoria.signals import (
                audit_post_save,
                audit_post_delete,
                pre_save_handler,
            )

            pre_save.connect(pre_save_handler, dispatch_uid="pre_save_audit")
            post_save.connect(audit_post_save, dispatch_uid="post_save_audit")
            post_delete.connect(audit_post_delete, dispatch_uid="post_delete_audit")
            print("✓ Señales de auditoría reconectadas correctamente")
        except (ImportError, KeyError) as e:
            print(f"! No se pudieron reconectar algunas señales de auditoría: {e}")


class CacheInterProcessCommunicationTest(RedisTestCase):
    """Test para verificar que Redis permite la comunicación entre procesos"""

    def test_redis_cache_interprocess(self):
        """Verifica que un proceso hijo puede escribir en Redis y el proceso principal puede leer"""
        # Crear una clave única para el test
        test_id = str(uuid.uuid4())
        cache_key = f"test_redis_{test_id}"
        test_data = {
            "message": "Este es un mensaje de prueba",
            "timestamp": time.time(),
            "is_epoch_log": True,
            "epoch_number": 42,
        }

        # Limpiar la cache por si acaso
        cache.delete(cache_key)

        # Verificar que la clave no existe al inicio
        initial_data = cache.get(cache_key)
        self.assertIsNone(initial_data, "La clave ya existe en cache antes del test")

        # Crear un proceso hijo para escribir en cache
        process = multiprocessing.Process(
            target=write_to_cache, args=(cache_key, test_data)
        )

        # Iniciar el proceso hijo y esperar a que termine
        process.start()
        process.join()

        # Verificar que el proceso principal puede leer los datos escritos por el hijo
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data, "No se pudo leer datos del cache compartido")
        self.assertEqual(
            cached_data["message"], test_data["message"], "El mensaje no coincide"
        )
        self.assertEqual(
            cached_data["is_epoch_log"],
            test_data["is_epoch_log"],
            "El flag is_epoch_log no coincide",
        )
        self.assertEqual(
            cached_data["epoch_number"],
            test_data["epoch_number"],
            "El número de época no coincide",
        )


class TrainingLogSystemTest(RedisTestCase):
    """Test para verificar el sistema completo de logs de entrenamiento"""

    def test_training_log_system(self):
        """Verifica que los logs de entrenamiento fluyan correctamente entre procesos"""
        # Importar la función que añade actualizaciones
        from .entrenamiento_utils import _add_update

        # Crear un ID único para este test
        training_id = f"test_{uuid.uuid4()}"

        # Configurar la cache inicial
        config_key = f"training_config_{training_id}"
        initial_config = {"status": "running", "updates": []}
        cache.set(config_key, initial_config, 3600)

        # Datos de prueba para un log de época
        epoch_log = {
            "type": "log",
            "message": "Época 5/100 - loss: 0.452 - val_loss: 0.487",
            "level": "info",
            "is_epoch_log": True,
            "is_real_epoch": True,
            "epoch_number": 5,
            "total_epochs": 100,
            "timestamp": time.time(),
        }

        # Crear un proceso hijo que simule el proceso de entrenamiento
        process = multiprocessing.Process(
            target=_add_update, args=(training_id, epoch_log)
        )

        # Iniciar proceso y esperar a que termine
        process.start()
        process.join()

        # Verificar que el log fue agregado correctamente a la cache compartida
        updated_config = cache.get(config_key)
        self.assertIsNotNone(updated_config, "No se encontró la configuración en cache")
        self.assertIn(
            "updates",
            updated_config,
            "No se encontró la lista de updates en la configuración",
        )
        self.assertTrue(
            len(updated_config["updates"]) > 0,
            "No hay actualizaciones en la configuración",
        )

        # Verificar si el log de época está presente
        found_log = False
        for update in updated_config["updates"]:
            if (
                update.get("is_epoch_log")
                and update.get("epoch_number") == 5
                and "Época 5/100" in update.get("message", "")
            ):
                found_log = True
                break

        self.assertTrue(
            found_log, "El log de época no fue encontrado en las actualizaciones"
        )

    @patch("redes_neuronales.views._stream_training_updates")
    def test_stream_updates_function(self, mock_stream):
        """Verifica que la función de streaming pueda leer correctamente los logs"""
        from django.contrib.sessions.backends.db import SessionStore
        from .views import _stream_training_updates

        # Restaurar la función original para este test específico
        mock_stream.side_effect = _stream_training_updates

        # Crear ID único para este test
        training_id = f"test_{uuid.uuid4()}"
        session = SessionStore()

        # Configurar datos iniciales en cache
        config_key = f"training_config_{training_id}"
        initial_config = {
            "status": "running",
            "updates": [
                {
                    "type": "log",
                    "message": "Inicio de entrenamiento",
                    "level": "info",
                    "timestamp": time.time(),
                },
                {
                    "type": "log",
                    "message": "Época 1/100 - loss: 0.854 - val_loss: 0.921",
                    "level": "info",
                    "is_epoch_log": True,
                    "is_real_epoch": True,
                    "epoch_number": 1,
                    "total_epochs": 100,
                    "timestamp": time.time(),
                },
            ],
        }

        # Guardar en cache
        cache.set(config_key, initial_config, 3600)

        # Añadir una actualización para simular el fin del entrenamiento
        # para que la función de streaming no se quede en bucle infinito
        config = cache.get(config_key)
        config["status"] = "completed"
        cache.set(config_key, config, 3600)

        # Crear un generador con la función de streaming
        stream_generator = _stream_training_updates(training_id, session)

        # Obtener algunos eventos del generador
        events = []
        for i in range(10):  # Intentar obtener algunos eventos con límite
            try:
                event = next(stream_generator)
                events.append(event)
            except StopIteration:
                break

        # Verificar que al menos se recibieron algunos eventos
        self.assertTrue(len(events) > 0, "No se recibieron eventos del generador")

        # Verificar que hay al menos un evento de log
        log_events = [e for e in events if "event: log" in e]
        self.assertTrue(len(log_events) > 0, "No se encontraron eventos de tipo log")

        # Verificar contenido relevante en los eventos
        has_epoch_log = False
        for event in events:
            if "Época 1/100" in event:
                has_epoch_log = True
                break

        self.assertTrue(
            has_epoch_log, "No se encontró el log de época esperado en los eventos"
        )

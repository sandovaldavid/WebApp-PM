import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from .rnn_model import AdvancedRNNEstimator
from .data_processor import DataProcessor
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import logging

# Importar modelos de Django
from dashboard.models import (
    Tarea,
    TipoTarea,
    Fase,
    Resultadosrnn,
    Modeloestimacionrnn,
    Tarearecurso,
    Recurso,
    Recursohumano,
    Requerimiento,
    HistorialEquipo,
)

# Configurar logging
logger = logging.getLogger(__name__)


class EstimacionTiempoService:
    """Servicio para integrar el modelo de estimación de tiempo con Django"""

    def __init__(self):
        """Inicializa el servicio cargando el modelo y los preprocesadores"""
        self.model_path = os.path.join(
            settings.BASE_DIR, 'redes_neuronales', 'estimacion_tiempo', 'models'
        )
        self.model_name = 'tiempo_estimator'
        self.model = None
        self.processor = None
        self.is_initialized = False

    def initialize(self):
        """Carga el modelo y los preprocesadores"""
        try:
            # Cargar el modelo
            self.model = AdvancedRNNEstimator.load(self.model_path, self.model_name)

            # Cargar los preprocesadores
            self.processor = DataProcessor()
            success = self.processor.load_preprocessors(self.model_path)

            if success:
                self.is_initialized = True
                return True
            return False

        except Exception as e:
            logger.error(f"Error al inicializar el servicio de estimación: {str(e)}")
            return False

    def extract_task_features(self, tarea_id):
        """Extrae características de una tarea desde la base de datos

        Args:
            tarea_id: ID de la tarea

        Returns:
            dict: Características de la tarea para el modelo
        """
        try:
            # Obtener la tarea
            tarea = Tarea.objects.get(idtarea=tarea_id)

            # Obtener tipo de tarea
            tipo_tarea = tarea.tipo_tarea.nombre if tarea.tipo_tarea else "Backend"

            # Obtener fase
            fase = tarea.fase.nombre if tarea.fase else "Construcción/Desarrollo"

            # Obtener recursos asignados
            recursos = Tarearecurso.objects.filter(idtarea=tarea)
            cantidad_recursos = recursos.count() or 1

            # Información de los recursos (hasta 3)
            carga_trabajo = [0, 0, 0]
            experiencia = [0, 0, 0]

            for i, recurso_asignacion in enumerate(recursos[:3]):
                recurso_humano = Recursohumano.objects.filter(
                    idrecurso=recurso_asignacion.idrecurso
                ).first()

                # Carga de trabajo del recurso
                carga_trabajo[i] = recurso_asignacion.idrecurso.carga_trabajo or 1

                # Experiencia del recurso
                experiencia[i] = recurso_asignacion.experiencia or 3

            # Obtener experiencia del equipo
            equipo_id = tarea.idrequerimiento.idproyecto.idequipo_id
            experiencia_equipo = 3  # Valor por defecto

            if equipo_id:
                historial = (
                    HistorialEquipo.objects.filter(idequipo_id=equipo_id)
                    .order_by('-fecha_registro')
                    .first()
                )
                if historial and historial.completitud_tareas is not None:
                    # Convertir la completitud a una escala de 1-5
                    experiencia_equipo = max(
                        1, min(5, int(historial.completitud_tareas * 5 + 0.5))
                    )

            # Obtener claridad de requisitos
            requerimiento = tarea.idrequerimiento
            claridad_requisitos = 0.7  # Valor por defecto medio-alto

            if requerimiento and requerimiento.keywords:
                # Si hay keywords, consideramos que hay mejor claridad
                # Calculamos en base a la cantidad y calidad de keywords
                keywords = requerimiento.keywords.split(',')
                if len(keywords) >= 5:
                    claridad_requisitos = 0.9  # Muy claro
                elif len(keywords) >= 3:
                    claridad_requisitos = 0.8  # Bastante claro

            # Obtener tamaño de la tarea
            tamaño_tarea = tarea.tamaño_estimado or 5  # Story points, valor por defecto

            # Complejidad de la tarea
            complejidad = tarea.dificultad or 3  # Valor por defecto medio

            # Crear diccionario de características
            features = {
                'Complejidad': complejidad,
                'Tipo_Tarea': tipo_tarea,
                'Fase_Tarea': fase,
                'Cantidad_Recursos': cantidad_recursos,
                'Carga_Trabajo_R1': carga_trabajo[0],
                'Experiencia_R1': experiencia[0],
                'Carga_Trabajo_R2': carga_trabajo[1],
                'Experiencia_R2': experiencia[1],
                'Carga_Trabajo_R3': carga_trabajo[2],
                'Experiencia_R3': experiencia[2],
                'Experiencia_Equipo': experiencia_equipo,
                'Claridad_Requisitos': claridad_requisitos,
                'Tamaño_Tarea': tamaño_tarea,
            }

            return features

        except Exception as e:
            logger.error(
                f"Error al extraer características de la tarea {tarea_id}: {str(e)}"
            )
            return None

    def estimate_task_time(self, tarea_id):
        """Estima el tiempo de ejecución de una tarea

        Args:
            tarea_id: ID de la tarea

        Returns:
            float: Tiempo estimado en horas
            dict: Características utilizadas para la estimación
        """
        if not self.is_initialized:
            success = self.initialize()
            if not success:
                logger.error("No se pudo inicializar el servicio de estimación")
                return None, None

        try:
            # Extraer características
            features = self.extract_task_features(tarea_id)
            if not features:
                return None, None

            # Procesar características para el modelo
            X = self.processor.process_single_task(features)

            # Realizar predicción
            prediction = self.model.predict(X, self.processor.feature_dims)

            # Redondear a 2 decimales para mejor interpretabilidad
            estimated_time = round(float(prediction[0]), 2)

            return estimated_time, features

        except Exception as e:
            logger.error(f"Error al estimar tiempo de la tarea {tarea_id}: {str(e)}")
            return None, None

    def save_estimation(self, tarea_id, estimated_time, features=None):
        """Guarda la estimación en la base de datos

        Args:
            tarea_id: ID de la tarea
            estimated_time: Tiempo estimado en horas
            features: Características utilizadas (opcional)

        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            with transaction.atomic():
                # Obtener o crear modelo de estimación RNN
                modelo, created = Modeloestimacionrnn.objects.get_or_create(
                    nombremodelo='RNN Avanzado',
                    defaults={
                        'descripcionmodelo': 'Modelo de red neuronal recurrente para estimación de tiempo',
                        'versionmodelo': '1.0',
                        'precision': 0.85,  # Precisión aproximada
                        'fechacreacion': timezone.now(),
                    },
                )

                if not created:
                    modelo.fechamodificacion = timezone.now()
                    modelo.save()

                # Crear o actualizar resultado de RNN
                resultado, created = Resultadosrnn.objects.update_or_create(
                    idtarea_id=tarea_id,
                    idmodelo=modelo.idmodelo,
                    defaults={
                        'duracionestimada': estimated_time,
                        'timestamp': timezone.now(),
                        'recursos': str(features) if features else None,
                    },
                )

                # Actualizar la tarea con la duración estimada
                tarea = Tarea.objects.get(idtarea=tarea_id)
                tarea.duracionestimada = estimated_time

                # Si no hay fecha de inicio/fin, sugerir fechas basadas en la estimación
                if not tarea.fechainicio:
                    tarea.fechainicio = timezone.now().date()
                if not tarea.fechafin and tarea.fechainicio:
                    # Calcular fecha fin basada en días hábiles (8 horas por día)
                    dias_estimados = max(1, round(estimated_time / 8))
                    from datetime import timedelta

                    tarea.fechafin = tarea.fechainicio + timedelta(days=dias_estimados)

                tarea.save()

                return True

        except Exception as e:
            logger.error(f"Error al guardar estimación para tarea {tarea_id}: {str(e)}")
            return False

    def estimate_and_save(self, tarea_id):
        """Estima el tiempo de una tarea y guarda el resultado

        Args:
            tarea_id: ID de la tarea

        Returns:
            tuple: (éxito, tiempo_estimado, mensaje)
        """
        estimated_time, features = self.estimate_task_time(tarea_id)

        if estimated_time is None:
            return False, None, "No se pudo estimar el tiempo para la tarea"

        success = self.save_estimation(tarea_id, estimated_time, features)

        if not success:
            return (
                False,
                estimated_time,
                "La estimación se realizó pero no se pudo guardar",
            )

        return True, estimated_time, "Estimación realizada y guardada correctamente"

    def estimate_project_completion(self, proyecto_id):
        """Estima el tiempo total para completar un proyecto

        Args:
            proyecto_id: ID del proyecto

        Returns:
            dict: Información sobre la estimación del proyecto
        """
        try:
            from django.db.models import Sum

            # Obtener todas las tareas del proyecto
            tareas = Tarea.objects.filter(
                idrequerimiento__idproyecto_id=proyecto_id
            ).select_related('idrequerimiento')

            # Contar tareas
            total_tareas = tareas.count()
            tareas_estimadas = tareas.exclude(duracionestimada=None).count()
            tareas_completadas = tareas.filter(estado='Completada').count()

            # Sumar tiempo estimado y actual
            tiempo_estimado_total = (
                tareas.aggregate(Sum('duracionestimada'))['duracionestimada__sum'] or 0
            )
            tiempo_actual_total = (
                tareas.aggregate(Sum('duracionactual'))['duracionactual__sum'] or 0
            )

            # Calcular porcentaje de completitud
            porcentaje_completitud = (
                (tareas_completadas / total_tareas * 100) if total_tareas > 0 else 0
            )

            # Calcular fecha estimada de finalización
            import datetime

            proyecto = (
                tareas.first().idrequerimiento.idproyecto if tareas.exists() else None
            )

            fecha_fin_estimada = None
            if proyecto and proyecto.fechainicio:
                # Calcular días laborables necesarios (asumiendo 8 horas por día)
                dias_necesarios = max(1, round(tiempo_estimado_total / 8))

                # Añadir a la fecha de inicio
                fecha_fin_estimada = proyecto.fechainicio + datetime.timedelta(
                    days=dias_necesarios
                )

            # Devolver resultados
            resultado = {
                'proyecto_id': proyecto_id,
                'nombre_proyecto': (
                    proyecto.nombreproyecto if proyecto else "Proyecto sin nombre"
                ),
                'total_tareas': total_tareas,
                'tareas_estimadas': tareas_estimadas,
                'tareas_completadas': tareas_completadas,
                'tiempo_estimado_total': tiempo_estimado_total,
                'tiempo_actual_total': tiempo_actual_total,
                'porcentaje_completitud': porcentaje_completitud,
                'fecha_fin_estimada': fecha_fin_estimada,
                'start_date': proyecto.fechainicio if proyecto else None,
            }

            return resultado

        except Exception as e:
            logger.error(
                f"Error al estimar completitud del proyecto {proyecto_id}: {str(e)}"
            )
            return None

    def reestimate_after_changes(self, tarea_id):
        """Reestima una tarea después de cambios en sus características

        Args:
            tarea_id: ID de la tarea

        Returns:
            dict: Resultado de la reestimación con comparación
        """
        try:
            # Obtener estimación previa
            resultados_previos = (
                Resultadosrnn.objects.filter(idtarea_id=tarea_id)
                .order_by('-timestamp')
                .first()
            )

            estimacion_previa = (
                resultados_previos.duracionestimada if resultados_previos else 0
            )

            # Realizar nueva estimación
            nueva_estimacion, features = self.estimate_task_time(tarea_id)

            if nueva_estimacion is None:
                return {
                    'status': 'error',
                    'message': 'No se pudo realizar la nueva estimación',
                }

            # Calcular diferencia porcentual
            if estimacion_previa > 0:
                diferencia_porcentual = (
                    (nueva_estimacion - estimacion_previa) / estimacion_previa
                ) * 100
            else:
                diferencia_porcentual = 100  # Si no había estimación previa

            # Guardar nueva estimación
            self.save_estimation(tarea_id, nueva_estimacion, features)

            return {
                'status': 'success',
                'estimacion_previa': estimacion_previa,
                'nueva_estimacion': nueva_estimacion,
                'diferencia_horas': nueva_estimacion - estimacion_previa,
                'diferencia_porcentual': diferencia_porcentual,
                'fecha_estimacion': timezone.now(),
            }

        except Exception as e:
            logger.error(f"Error en reestimación de tarea {tarea_id}: {str(e)}")
            return {'status': 'error', 'message': f"Error en reestimación: {str(e)}"}

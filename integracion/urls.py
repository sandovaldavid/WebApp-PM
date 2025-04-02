from django.urls import path

from . import views

app_name = "integracion"
urlpatterns = [
    path("", views.index, name="index"),
    # Configuración Jira
    path("jira/configurar/", views.configurar_jira, name="configurar_jira"),
    path("jira/proyectos/", views.listar_proyectos_jira, name="listar_proyectos_jira"),
    path("jira/mapear-proyecto/", views.mapear_proyecto, name="mapear_proyecto"),
    path("jira/sincronizar/", views.sincronizar_jira, name="sincronizar_jira"),
    
    # Nuevos endpoints para funcionalidades adicionales
    path("jira/usuarios/", views.listar_usuarios_jira, name="listar_usuarios_jira"),
    path("jira/mapear-usuarios/", views.mapear_usuarios_jira, name="mapear_usuarios_jira"),
    path("jira/limpiar-mapeos/", views.limpiar_mapeos_huerfanos, name="limpiar_mapeos_huerfanos"),
    path("jira/estado-salud/", views.verificar_salud_integracion, name="verificar_salud_integracion"),
    path("jira/reporte-sincronizacion/", views.generar_reporte_sincronizacion, name="generar_reporte_sincronizacion"),
    path("jira/configuracion-avanzada/", views.configuracion_avanzada_jira, name="configuracion_avanzada_jira"),
    path("jira/diagnostico-campos/", views.diagnosticar_campos_jira, name="diagnosticar_campos_jira"),
    
    # Rutas para componentes HTML
    path("templates/project-mapping/", views.project_mapping_template, name="project_mapping_template"),
    path("templates/user-mapping/", views.user_mapping_template, name="user_mapping_template"),
    path("templates/health-check/", views.health_check_template, name="health_check_template"),
    path("templates/sync-report/", views.sync_report_template, name="sync_report_template"),
]

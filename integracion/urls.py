from django.urls import path

from . import views

app_name = "integracion"
urlpatterns = [
    path("", views.index, name="index"),
    path("jira/configurar/", views.configurar_jira, name="configurar_jira"),
    path("jira/proyectos/", views.listar_proyectos_jira, name="listar_proyectos_jira"),
    path("jira/mapear-proyecto/", views.mapear_proyecto, name="mapear_proyecto"),
    path("jira/sincronizar/", views.sincronizar_jira, name="sincronizar_jira"),
]

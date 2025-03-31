from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from dashboard.models import Equipo, Miembro, Recurso, HistorialEquipo
from api.permissions import IsAdminOrReadOnly
from api.serializers.equipo_serializers import EquipoSerializer, EquipoDetailSerializer


class EquipoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para equipos que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar equipos.
    """

    queryset = Equipo.objects.all().order_by("-fechacreacion")
    serializer_class = EquipoSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["nombreequipo", "descripcion"]
    ordering_fields = ["nombreequipo", "fechacreacion", "fechamodificacion"]

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == "retrieve":
            return EquipoDetailSerializer
        return EquipoSerializer

    @action(detail=True, methods=["get"])
    def miembros(self, request, pk=None):
        """Get all members of a specific team"""
        equipo = self.get_object()
        miembros = Miembro.objects.filter(idequipo=equipo)

        miembros_data = []
        for miembro in miembros:
            recurso = miembro.idrecurso
            miembro_info = {
                "idmiembro": miembro.idmiembro,
                "recurso": {
                    "idrecurso": recurso.idrecurso,
                    "nombrerecurso": recurso.nombrerecurso,
                    "tipo": recurso.idtiporecurso.nametiporecurso,
                },
            }
            miembros_data.append(miembro_info)

        return Response(miembros_data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def agregar_miembro(self, request, pk=None):
        """Add a new member to the team"""
        equipo = self.get_object()
        idrecurso = request.data.get("idrecurso")

        if not idrecurso:
            return Response(
                {"error": "Se requiere el ID del recurso"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            recurso = Recurso.objects.get(idrecurso=idrecurso)
        except Recurso.DoesNotExist:
            return Response(
                {"error": "El recurso especificado no existe"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verificar si ya es miembro del equipo
        if Miembro.objects.filter(idequipo=equipo, idrecurso=recurso).exists():
            return Response(
                {"error": "El recurso ya es miembro de este equipo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Crear el nuevo miembro
        miembro = Miembro.objects.create(idequipo=equipo, idrecurso=recurso)

        return Response(
            {"mensaje": "Miembro agregado con éxito", "idmiembro": miembro.idmiembro},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True, methods=["delete"], permission_classes=[permissions.IsAdminUser]
    )
    def eliminar_miembro(self, request, pk=None):
        """Remove a member from the team"""
        equipo = self.get_object()
        idmiembro = request.data.get("idmiembro")

        if not idmiembro:
            return Response(
                {"error": "Se requiere el ID del miembro"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            miembro = Miembro.objects.get(idmiembro=idmiembro, idequipo=equipo)
            miembro.delete()
            return Response(
                {"mensaje": "Miembro eliminado con éxito"}, status=status.HTTP_200_OK
            )
        except Miembro.DoesNotExist:
            return Response(
                {"error": "El miembro especificado no existe en este equipo"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        """Get performance history of the team"""
        equipo = self.get_object()
        historial = HistorialEquipo.objects.filter(idequipo=equipo).order_by(
            "-fecha_registro"
        )

        historial_data = []
        for registro in historial:
            historial_data.append(
                {
                    "id": registro.idhistorialequipo,
                    "completitud_tareas": registro.completitud_tareas,
                    "tiempo_promedio_tareas": registro.tiempo_promedio_tareas,
                    "fecha_registro": registro.fecha_registro,
                }
            )

        return Response(historial_data)

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from dashboard.models import Requerimiento, Tarea
from api.permissions import IsAdminOrReadOnly
from api.serializers.requerimiento_serializers import RequerimientoSerializer, RequerimientoListSerializer
from api.pagination import CustomPagination


class RequerimientoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para requerimientos que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar requerimientos.
    """
    
    queryset = Requerimiento.objects.all().order_by('-fechacreacion')
    serializer_class = RequerimientoSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['idproyecto']
    search_fields = ['descripcion', 'keywords']
    ordering_fields = ['fechacreacion', 'fechamodificacion']
    
    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'list':
            return RequerimientoListSerializer
        return RequerimientoSerializer
    
    def perform_create(self, serializer):
        """Custom create logic if needed"""
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def tareas(self, request, pk=None):
        """Get all tasks related to this requirement"""
        requerimiento = self.get_object()
        tareas = Tarea.objects.filter(idrequerimiento=requerimiento)
        
        from api.serializers.tarea_serializers import TareaListSerializer
        serializer = TareaListSerializer(tareas, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_proyecto(self, request):
        """Get requirements filtered by project"""
        proyecto_id = request.query_params.get('idproyecto')
        if not proyecto_id:
            return Response(
                {"error": "Se requiere el parámetro 'idproyecto'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        requerimientos = Requerimiento.objects.filter(idproyecto=proyecto_id)
        page = self.paginate_queryset(requerimientos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(requerimientos, many=True)
        return Response(serializer.data)

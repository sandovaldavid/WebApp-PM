from django_filters import rest_framework as filters
from dashboard.models import Recurso


class RecursoFilter(filters.FilterSet):
    """
    Filtro personalizado para recursos que permite filtrar por:
    - disponibilidad: True/False
    - tipo: 'humano' o 'material'
    - idtiporecurso: ID del tipo de recurso
    """

    tipo = filters.CharFilter(method="filter_by_tipo")
    disponible = filters.BooleanFilter(field_name="disponibilidad")

    class Meta:
        model = Recurso
        fields = ["disponibilidad", "idtiporecurso", "tipo"]

    def filter_by_tipo(self, queryset, name, value):
        """
        Filtrar recursos por tipo 'humano' o 'material'
        """
        if value.lower() == "humano":
            return queryset.filter(recursohumano__isnull=False)
        elif value.lower() == "material":
            return queryset.filter(recursomaterial__isnull=False)
        return queryset

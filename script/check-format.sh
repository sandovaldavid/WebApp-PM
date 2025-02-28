#!/bin/bash

# Define colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin Color

echo -e "${YELLOW}=== Verificando formato del código Python con Black ===${NC}"
echo ""

# Variable para rastrear errores
ERRORS=0

# Verificar archivos Python con Black (modo check)
if python -m black --check . ; then
    echo -e "${GREEN}✓ Black: Todos los archivos Python tienen el formato correcto.${NC}"
    echo -e "${GREEN}✓ El código cumple con los estándares de formato de Python.${NC}"
    exit 0
else
    echo -e "${RED}✗ Black: Se encontraron archivos Python con formato incorrecto.${NC}"
    echo -e "${YELLOW}Para ver detalles específicos, ejecuta:${NC} black --diff ."
    echo -e "${YELLOW}Para corregir automáticamente los problemas:${NC} ./script/format.sh"
    exit 1
fi
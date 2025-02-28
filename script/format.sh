#!/bin/bash

echo "Formateando archivos Python con Black..."
black .

echo "Formateando archivos HTML, JS y CSS con Prettier..."
npx prettier --write "**/*.{js,html,css}"

echo "¡Formateo completado!"
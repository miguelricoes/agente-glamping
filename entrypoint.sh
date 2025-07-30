#!/bin/sh
# Ejecuta Gunicorn con el puerto asignado por Railway (o 8080 por defecto)
exec gunicorn --bind 0.0.0.0:${PORT:-8080} agente:app

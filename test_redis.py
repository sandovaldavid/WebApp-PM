# Guardar como test_redis.py en la raíz del proyecto
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.core.cache import cache

# Probar escritura
cache.set('test_key', 'Redis está funcionando!', 60)

# Probar lectura
value = cache.get('test_key')
print(f"Valor leído de Redis: {value}")
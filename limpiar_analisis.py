#!/usr/bin/env python
"""
Script para limpiar todos los análisis antiguos y empezar con datos frescos.

Uso:
    python limpiar_analisis.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'asistente'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
os.environ['DJANGO_READ_DOT_ENV_FILE'] = 'True'

django.setup()

from analisis_coples.models import AnalisisCople, SegmentacionDefecto, SegmentacionPieza

def limpiar_datos():
    """Elimina todos los análisis y sus segmentaciones relacionadas"""
    
    print("🧹 Limpiando datos antiguos...")
    print("")
    
    # Contar registros actuales
    total_analisis = AnalisisCople.objects.count()
    total_defectos = SegmentacionDefecto.objects.count()
    total_piezas = SegmentacionPieza.objects.count()
    
    print(f"📊 Estado actual:")
    print(f"   - Análisis: {total_analisis}")
    print(f"   - Segmentaciones de defectos: {total_defectos}")
    print(f"   - Segmentaciones de piezas: {total_piezas}")
    print("")
    
    if total_analisis == 0:
        print("✅ No hay datos que limpiar")
        return
    
    # Confirmar
    respuesta = input("⚠️  ¿Estás seguro de eliminar TODOS los análisis? (si/no): ")
    
    if respuesta.lower() not in ['si', 'sí', 's', 'y', 'yes']:
        print("❌ Operación cancelada")
        return
    
    print("")
    print("🗑️  Eliminando datos...")
    
    # Eliminar en orden (las segmentaciones se eliminarán en cascada)
    AnalisisCople.objects.all().delete()
    
    print("")
    print("✅ Datos eliminados correctamente")
    print("")
    print("📊 Estado final:")
    print(f"   - Análisis: {AnalisisCople.objects.count()}")
    print(f"   - Segmentaciones de defectos: {SegmentacionDefecto.objects.count()}")
    print(f"   - Segmentaciones de piezas: {SegmentacionPieza.objects.count()}")
    print("")
    print("🎯 Ahora puedes empezar con datos frescos")

if __name__ == '__main__':
    limpiar_datos()


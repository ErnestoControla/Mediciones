#!/usr/bin/env python
"""
Script de prueba para el módulo de mediciones geométricas.

Prueba el cálculo de dimensiones con máscaras sintéticas.
"""

import numpy as np
import cv2
import sys
import os

# Agregar paths necesarios
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'asistente'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

from analisis_coples.modules.measurements import get_measurement_service

def crear_mascara_rectangular(ancho: int, alto: int, tam_imagen: int = 640) -> np.ndarray:
    """Crea una máscara rectangular para pruebas"""
    mascara = np.zeros((tam_imagen, tam_imagen), dtype=np.uint8)
    x_inicio = (tam_imagen - ancho) // 2
    y_inicio = (tam_imagen - alto) // 2
    mascara[y_inicio:y_inicio+alto, x_inicio:x_inicio+ancho] = 255
    return mascara

def crear_mascara_circular(radio: int, tam_imagen: int = 640) -> np.ndarray:
    """Crea una máscara circular para pruebas"""
    mascara = np.zeros((tam_imagen, tam_imagen), dtype=np.uint8)
    centro = (tam_imagen // 2, tam_imagen // 2)
    cv2.circle(mascara, centro, radio, 255, -1)
    return mascara

def test_mediciones():
    """Prueba el cálculo de mediciones"""
    
    print("\n" + "="*60)
    print("🧪 TEST DEL MÓDULO DE MEDICIONES GEOMÉTRICAS")
    print("="*60 + "\n")
    
    # Obtener servicio
    service = get_measurement_service()
    
    # Test 1: Rectángulo 200x100
    print("📊 Test 1: Rectángulo 200x100 píxeles")
    print("-" * 60)
    mascara_rect = crear_mascara_rectangular(200, 100)
    mediciones_rect = service.calcular_mediciones_completas(mascara_rect)
    
    print(f"✅ Ancho BBox: {mediciones_rect['ancho_bbox_px']:.2f} px (esperado: ~200)")
    print(f"✅ Alto BBox: {mediciones_rect['alto_bbox_px']:.2f} px (esperado: ~100)")
    print(f"✅ Área: {mediciones_rect['area_mascara_px']:.0f} px² (esperado: ~20000)")
    print(f"✅ Perímetro: {mediciones_rect['perimetro_mascara_px']:.2f} px (esperado: ~600)")
    print(f"✅ Excentricidad: {mediciones_rect['excentricidad']:.3f} (esperado: ~0.866 para rectángulo 2:1)")
    print(f"✅ Orientación: {mediciones_rect['orientacion_grados']:.2f}°\n")
    
    # Test 2: Círculo radio 100
    print("📊 Test 2: Círculo radio 100 píxeles")
    print("-" * 60)
    mascara_circ = crear_mascara_circular(100)
    mediciones_circ = service.calcular_mediciones_completas(mascara_circ)
    
    print(f"✅ Ancho BBox: {mediciones_circ['ancho_bbox_px']:.2f} px (esperado: ~200)")
    print(f"✅ Alto BBox: {mediciones_circ['alto_bbox_px']:.2f} px (esperado: ~200)")
    print(f"✅ Área: {mediciones_circ['area_mascara_px']:.0f} px² (esperado: ~31416 = π*100²)")
    print(f"✅ Perímetro: {mediciones_circ['perimetro_mascara_px']:.2f} px (esperado: ~628 = 2π*100)")
    print(f"✅ Excentricidad: {mediciones_circ['excentricidad']:.3f} (esperado: ~0 para círculo)")
    print(f"✅ Orientación: {mediciones_circ['orientacion_grados']:.2f}°\n")
    
    # Test 3: Conversión a milímetros
    print("📊 Test 3: Conversión píxeles → milímetros")
    print("-" * 60)
    factor_mm = 0.1  # 1 píxel = 0.1 mm
    service.set_conversion_factor(factor_mm)
    
    mediciones_mm = service.calcular_mediciones_completas(mascara_rect, convertir_a_mm=True)
    
    print(f"Factor de conversión: {factor_mm} mm/px")
    print(f"✅ Ancho: {mediciones_mm['ancho_bbox_px']:.2f} px → {mediciones_mm.get('ancho_bbox_mm', 0):.2f} mm")
    print(f"✅ Alto: {mediciones_mm['alto_bbox_px']:.2f} px → {mediciones_mm.get('alto_bbox_mm', 0):.2f} mm")
    print(f"✅ Área: {mediciones_mm['area_mascara_px']:.0f} px² → {mediciones_mm.get('area_mascara_mm', 0):.2f} mm²")
    print(f"✅ Perímetro: {mediciones_mm['perimetro_mascara_px']:.2f} px → {mediciones_mm.get('perimetro_mascara_mm', 0):.2f} mm\n")
    
    # Validaciones
    print("="*60)
    print("🔍 VALIDACIÓN DE RESULTADOS")
    print("="*60 + "\n")
    
    validaciones_ok = True
    
    # Validar rectángulo
    if abs(mediciones_rect['ancho_bbox_px'] - 200) > 5:
        print(f"❌ Error en ancho de rectángulo: {mediciones_rect['ancho_bbox_px']}")
        validaciones_ok = False
    else:
        print(f"✅ Ancho de rectángulo correcto")
    
    if abs(mediciones_rect['alto_bbox_px'] - 100) > 5:
        print(f"❌ Error en alto de rectángulo: {mediciones_rect['alto_bbox_px']}")
        validaciones_ok = False
    else:
        print(f"✅ Alto de rectángulo correcto")
    
    # Validar círculo
    if abs(mediciones_circ['excentricidad']) > 0.1:
        print(f"❌ Error en excentricidad de círculo: {mediciones_circ['excentricidad']} (debería ser ~0)")
        validaciones_ok = False
    else:
        print(f"✅ Excentricidad de círculo correcta")
    
    # Validar conversión mm
    if abs(mediciones_mm.get('ancho_bbox_mm', 0) - 20.0) > 1.0:
        print(f"❌ Error en conversión a mm: {mediciones_mm.get('ancho_bbox_mm', 0)} (esperado: ~20)")
        validaciones_ok = False
    else:
        print(f"✅ Conversión a milímetros correcta")
    
    print("\n" + "="*60)
    if validaciones_ok:
        print("🎉 TODOS LOS TESTS PASARON CORRECTAMENTE")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*60 + "\n")
    
    return validaciones_ok

if __name__ == "__main__":
    exito = test_mediciones()
    sys.exit(0 if exito else 1)


#!/usr/bin/env python
"""
Script para probar _generate_mask() de forma aislada y diagnosticar el segfault.

Uso:
    python test_generate_mask.py
"""

import numpy as np
import cv2
import sys

def sigmoid(x):
    """Función sigmoid segura"""
    return 1 / (1 + np.exp(-np.clip(x, -250, 250)))

def test_generate_mask_v1_dot(mask_coeffs, mask_protos, bbox, input_shape):
    """
    Versión 1: Usando np.dot (la que está en el código actual)
    """
    print("\n" + "="*70)
    print("🧪 TEST 1: np.dot (versión actual)")
    print("="*70)
    
    try:
        print("📊 Inputs:")
        print(f"   mask_coeffs shape: {mask_coeffs.shape}, dtype: {mask_coeffs.dtype}")
        print(f"   mask_protos shape: {mask_protos.shape}, dtype: {mask_protos.dtype}")
        print(f"   bbox: {bbox}")
        print(f"   input_shape: {input_shape}")
        
        # Paso 1: Extraer prototipos
        print("\n📍 Paso 1: Extraer prototipos...")
        protos = mask_protos[0]  # Shape: [32, 160, 160]
        print(f"   ✅ protos shape: {protos.shape}")
        
        # Paso 2: Reshape
        print("\n📍 Paso 2: Reshape para np.dot...")
        protos_reshaped = protos.reshape(32, -1)  # Shape: [32, 160*160]
        print(f"   ✅ protos_reshaped shape: {protos_reshaped.shape}")
        
        # Paso 3: np.dot (AQUÍ PUEDE CRASHEAR)
        print("\n📍 Paso 3: np.dot (CRÍTICO)...")
        mask_flat = np.dot(mask_coeffs, protos_reshaped)  # Shape: [160*160]
        print(f"   ✅ mask_flat shape: {mask_flat.shape}")
        
        # Paso 4: Reshape a 2D
        print("\n📍 Paso 4: Reshape a 2D...")
        mask = mask_flat.reshape(160, 160)  # Shape: [160, 160]
        print(f"   ✅ mask shape: {mask.shape}")
        
        # Paso 5: Sigmoid
        print("\n📍 Paso 5: Aplicar sigmoid...")
        mask = sigmoid(mask)
        print(f"   ✅ mask después de sigmoid: min={mask.min():.3f}, max={mask.max():.3f}")
        
        # Paso 6: Resize
        print("\n📍 Paso 6: Redimensionar a input_shape...")
        H, W = input_shape
        if mask.shape != (H, W):
            mask = cv2.resize(mask, (W, H))
        print(f"   ✅ mask redimensionada: {mask.shape}")
        
        # Paso 7: Crop al bbox
        print("\n📍 Paso 7: Recortar al bbox...")
        x1, y1, x2, y2 = map(int, bbox)
        mask_cropped = np.zeros_like(mask)
        
        if x1 < W and y1 < H and x2 > 0 and y2 > 0:
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(W, x2)
            y2 = min(H, y2)
            
            bbox_mask = mask[y1:y2, x1:x2]
            bbox_mask_binary = (bbox_mask > 0.5).astype(np.float32)
            mask_cropped[y1:y2, x1:x2] = bbox_mask_binary
        
        pixels_activos = np.sum(mask_cropped > 0.5)
        print(f"   ✅ mask_cropped: {mask_cropped.shape}, píxeles activos: {pixels_activos}")
        
        print("\n✅ TEST 1 EXITOSO - np.dot funciona")
        return mask_cropped
        
    except Exception as e:
        print(f"\n❌ TEST 1 FALLÓ: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_generate_mask_v2_tensordot(mask_coeffs, mask_protos, bbox, input_shape):
    """
    Versión 2: Usando np.tensordot (alternativa)
    """
    print("\n" + "="*70)
    print("🧪 TEST 2: np.tensordot (alternativa)")
    print("="*70)
    
    try:
        print("📊 Inputs:")
        print(f"   mask_coeffs shape: {mask_coeffs.shape}, dtype: {mask_coeffs.dtype}")
        print(f"   mask_protos shape: {mask_protos.shape}, dtype: {mask_protos.dtype}")
        
        # Paso 1: Extraer prototipos
        print("\n📍 Paso 1: Extraer prototipos...")
        protos = mask_protos[0]  # Shape: [32, 160, 160]
        print(f"   ✅ protos shape: {protos.shape}")
        
        # Paso 2: np.tensordot (PUEDE CRASHEAR)
        print("\n📍 Paso 2: np.tensordot (CRÍTICO)...")
        mask = np.tensordot(mask_coeffs, protos, axes=([0], [0]))  # Shape: [160, 160]
        print(f"   ✅ mask shape: {mask.shape}")
        
        # Paso 3: Sigmoid
        print("\n📍 Paso 3: Aplicar sigmoid...")
        mask = sigmoid(mask)
        print(f"   ✅ mask después de sigmoid: min={mask.min():.3f}, max={mask.max():.3f}")
        
        # Resto del procesamiento...
        H, W = input_shape
        if mask.shape != (H, W):
            mask = cv2.resize(mask, (W, H))
        
        x1, y1, x2, y2 = map(int, bbox)
        mask_cropped = np.zeros_like(mask)
        
        if x1 < W and y1 < H and x2 > 0 and y2 > 0:
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(W, x2)
            y2 = min(H, y2)
            
            bbox_mask = mask[y1:y2, x1:x2]
            bbox_mask_binary = (bbox_mask > 0.5).astype(np.float32)
            mask_cropped[y1:y2, x1:x2] = bbox_mask_binary
        
        pixels_activos = np.sum(mask_cropped > 0.5)
        print(f"   ✅ mask_cropped: {mask_cropped.shape}, píxeles activos: {pixels_activos}")
        
        print("\n✅ TEST 2 EXITOSO - np.tensordot funciona")
        return mask_cropped
        
    except Exception as e:
        print(f"\n❌ TEST 2 FALLÓ: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_generate_mask_v3_einsum(mask_coeffs, mask_protos, bbox, input_shape):
    """
    Versión 3: Usando np.einsum (más explícito y seguro)
    """
    print("\n" + "="*70)
    print("🧪 TEST 3: np.einsum (más seguro)")
    print("="*70)
    
    try:
        print("📊 Inputs:")
        print(f"   mask_coeffs shape: {mask_coeffs.shape}, dtype: {mask_coeffs.dtype}")
        print(f"   mask_protos shape: {mask_protos.shape}, dtype: {mask_protos.dtype}")
        
        # Paso 1: Extraer prototipos
        print("\n📍 Paso 1: Extraer prototipos...")
        protos = mask_protos[0]  # Shape: [32, 160, 160]
        print(f"   ✅ protos shape: {protos.shape}")
        
        # Paso 2: np.einsum (MÁS SEGURO)
        print("\n📍 Paso 2: np.einsum (CRÍTICO)...")
        # 'c,chw->hw' significa: sumar sobre dimensión c (32 canales)
        mask = np.einsum('c,chw->hw', mask_coeffs, protos)  # Shape: [160, 160]
        print(f"   ✅ mask shape: {mask.shape}")
        
        # Paso 3: Sigmoid
        print("\n📍 Paso 3: Aplicar sigmoid...")
        mask = sigmoid(mask)
        print(f"   ✅ mask después de sigmoid: min={mask.min():.3f}, max={mask.max():.3f}")
        
        # Resto del procesamiento...
        H, W = input_shape
        if mask.shape != (H, W):
            mask = cv2.resize(mask, (W, H))
        
        x1, y1, x2, y2 = map(int, bbox)
        mask_cropped = np.zeros_like(mask)
        
        if x1 < W and y1 < H and x2 > 0 and y2 > 0:
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(W, x2)
            y2 = min(H, y2)
            
            bbox_mask = mask[y1:y2, x1:x2]
            bbox_mask_binary = (bbox_mask > 0.5).astype(np.float32)
            mask_cropped[y1:y2, x1:x2] = bbox_mask_binary
        
        pixels_activos = np.sum(mask_cropped > 0.5)
        print(f"   ✅ mask_cropped: {mask_cropped.shape}, píxeles activos: {pixels_activos}")
        
        print("\n✅ TEST 3 EXITOSO - np.einsum funciona")
        return mask_cropped
        
    except Exception as e:
        print(f"\n❌ TEST 3 FALLÓ: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Función principal de prueba
    """
    print("🚀 Iniciando pruebas de generación de máscaras con prototipos YOLO11")
    print("="*70)
    
    # Crear datos sintéticos similares a los reales de YOLO11
    print("\n📦 Creando datos sintéticos...")
    
    # Coeficientes de máscara (32 valores)
    mask_coeffs = np.random.randn(32).astype(np.float32)
    
    # Prototipos de máscara (1, 32, 160, 160)
    mask_protos = np.random.randn(1, 32, 160, 160).astype(np.float32)
    
    # Bbox de ejemplo
    bbox = (100, 100, 300, 300)
    
    # Tamaño de imagen
    input_shape = (640, 640)
    
    print(f"✅ Datos creados:")
    print(f"   mask_coeffs: {mask_coeffs.shape}, dtype: {mask_coeffs.dtype}")
    print(f"   mask_protos: {mask_protos.shape}, dtype: {mask_protos.dtype}")
    print(f"   bbox: {bbox}")
    print(f"   input_shape: {input_shape}")
    
    # Probar todas las versiones
    resultados = {}
    
    # Test 1: np.dot
    result1 = test_generate_mask_v1_dot(mask_coeffs, mask_protos, bbox, input_shape)
    resultados['v1_dot'] = result1 is not None
    
    # Test 2: np.tensordot
    result2 = test_generate_mask_v2_tensordot(mask_coeffs, mask_protos, bbox, input_shape)
    resultados['v2_tensordot'] = result2 is not None
    
    # Test 3: np.einsum
    result3 = test_generate_mask_v3_einsum(mask_coeffs, mask_protos, bbox, input_shape)
    resultados['v3_einsum'] = result3 is not None
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*70)
    for version, exito in resultados.items():
        estado = "✅ FUNCIONA" if exito else "❌ FALLA"
        print(f"   {version}: {estado}")
    
    # Comparar resultados si todos funcionaron
    if all(resultados.values()):
        print("\n🎯 TODOS LOS MÉTODOS FUNCIONAN - Comparando resultados...")
        
        # Comparar máscaras
        diff_1_2 = np.abs(result1 - result2).max() if result1 is not None and result2 is not None else None
        diff_1_3 = np.abs(result1 - result3).max() if result1 is not None and result3 is not None else None
        diff_2_3 = np.abs(result2 - result3).max() if result2 is not None and result3 is not None else None
        
        print(f"   Diferencia máxima v1 vs v2: {diff_1_2}")
        print(f"   Diferencia máxima v1 vs v3: {diff_1_3}")
        print(f"   Diferencia máxima v2 vs v3: {diff_2_3}")
        
        if diff_1_2 < 0.01 and diff_1_3 < 0.01 and diff_2_3 < 0.01:
            print("\n   ✅ TODOS LOS MÉTODOS PRODUCEN RESULTADOS SIMILARES")
        else:
            print("\n   ⚠️  LOS MÉTODOS PRODUCEN RESULTADOS DIFERENTES")
    
    print("\n" + "="*70)
    print("🏁 PRUEBAS COMPLETADAS")
    print("="*70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


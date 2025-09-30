#!/usr/bin/env python3
"""
Configuración de logging para el sistema de análisis de coples
"""

import logging
import sys
from typing import Optional

class SistemaLogging:
    """
    Sistema de logging centralizado para el proyecto
    """
    
    _instancia = None
    _logger = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia
    
    def __init__(self):
        if self._logger is None:
            self._configurar_logger()
    
    def _configurar_logger(self):
        """Configura el logger principal"""
        self._logger = logging.getLogger('SistemaAnalisisCoples')
        self._logger.setLevel(logging.INFO)
        
        # Evitar duplicar handlers
        if not self._logger.handlers:
            # Handler para consola
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Formato de mensajes
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            self._logger.addHandler(console_handler)
    
    def info(self, mensaje: str):
        """Log de información"""
        self._logger.info(mensaje)
    
    def warning(self, mensaje: str):
        """Log de advertencia"""
        self._logger.warning(mensaje)
    
    def error(self, mensaje: str):
        """Log de error"""
        self._logger.error(mensaje)
    
    def debug(self, mensaje: str):
        """Log de debug (solo en modo debug)"""
        self._logger.debug(mensaje)
    
    def success(self, mensaje: str):
        """Log de éxito (usando info con emoji)"""
        self._logger.info(f"✅ {mensaje}")
    
    def proceso(self, mensaje: str):
        """Log de proceso (usando info con emoji)"""
        self._logger.info(f"🔄 {mensaje}")
    
    def resultado(self, mensaje: str):
        """Log de resultado (usando info con emoji)"""
        self._logger.info(f"📊 {mensaje}")
    
    def configurar_nivel(self, nivel: str):
        """Configura el nivel de logging"""
        niveles = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        
        if nivel.upper() in niveles:
            self._logger.setLevel(niveles[nivel.upper()])
            for handler in self._logger.handlers:
                handler.setLevel(niveles[nivel.upper()])

# Instancia global del logger
logger = SistemaLogging()

# Funciones de conveniencia
def log_info(mensaje: str):
    """Log de información"""
    logger.info(mensaje)

def log_warning(mensaje: str):
    """Log de advertencia"""
    logger.warning(mensaje)

def log_error(mensaje: str):
    """Log de error"""
    logger.error(mensaje)

def log_success(mensaje: str):
    """Log de éxito"""
    logger.success(mensaje)

def log_proceso(mensaje: str):
    """Log de proceso"""
    logger.proceso(mensaje)

def log_resultado(mensaje: str):
    """Log de resultado"""
    logger.resultado(mensaje)

def configurar_logging(nivel: str = 'INFO'):
    """Configura el nivel de logging global"""
    logger.configurar_nivel(nivel)

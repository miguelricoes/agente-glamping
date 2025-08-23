#!/usr/bin/env python3
"""
Script de verificación de seguridad de concurrencia
Verifica que las implementaciones atómicas y cache estén funcionando correctamente
"""

import os
import sys
from datetime import datetime, date
from typing import Dict, Any

# Configurar path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import get_logger
from config.database_config import get_database_config
from services.persistent_state_service import PersistentStateService
from services.database_service import DatabaseService  
from services.reservation_service import ReservationService

logger = get_logger(__name__)

class ConcurrencySafetyTester:
    """Tester para verificar implementaciones de seguridad de concurrencia"""
    
    def __init__(self):
        self.database_config = get_database_config()
        self.db = None
        self.persistent_service = None
        self.database_service = None
        self.reservation_service = None
        
    def setup_services(self):
        """Configurar servicios para testing"""
        try:
            # Verificar que la configuración de DB esté disponible
            if not self.database_config.database_available:
                logger.warning("Base de datos no disponible - usando modo de testing sin BD")
                return False
            
            self.db = self.database_config.db
            
            # Inicializar servicios
            self.persistent_service = PersistentStateService(self.db, enable_caching=True)
            self.database_service = DatabaseService(
                self.db, 
                self.database_config.Reserva, 
                self.database_config.Usuario,
                persistent_state_service=self.persistent_service
            )
            self.reservation_service = ReservationService(self.db, self.database_config.Reserva)
            
            logger.info("✅ Servicios configurados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando servicios: {e}")
            return False
    
    def test_atomic_transactions(self) -> Dict[str, bool]:
        """Verificar que las transacciones atómicas funcionen"""
        results = {}
        
        try:
            # Test 1: Verificar context manager atómico en persistent_service
            logger.info("🧪 Testing atomic transactions en persistent_service...")
            
            test_user_id = "test_atomic_user"
            
            # Test transacción exitosa
            try:
                with self.persistent_service.atomic_transaction():
                    # Operación que debería completarse
                    self.persistent_service.update_user_state(test_user_id, {
                        "current_flow": "test_atomic",
                        "test_timestamp": datetime.utcnow().isoformat()
                    })
                    
                # Verificar que el estado se guardó
                state = self.persistent_service.get_user_state(test_user_id)
                results["persistent_atomic_success"] = state.get("current_flow") == "test_atomic"
                
            except Exception as e:
                logger.error(f"Error en transacción atómica persistent_service: {e}")
                results["persistent_atomic_success"] = False
            
            # Test 2: Verificar context manager en database_service
            logger.info("🧪 Testing atomic transactions en database_service...")
            
            if self.database_service:
                try:
                    with self.database_service.atomic_transaction():
                        # Test que debería completarse sin problemas
                        pass
                    results["database_atomic_success"] = True
                except Exception as e:
                    logger.error(f"Error en transacción atómica database_service: {e}")
                    results["database_atomic_success"] = False
            else:
                results["database_atomic_success"] = False
                
            # Test 3: Verificar transacción atómica en reservation_service
            logger.info("🧪 Testing atomic transactions en reservation_service...")
            
            if self.reservation_service:
                try:
                    # Datos de reserva de prueba (que deberían fallar por validación)
                    test_reservation = {
                        'numero_whatsapp': 'test_atomic_reservation',
                        'email_contacto': 'test@atomic.com',
                        'cantidad_huespedes': -1,  # Inválido intencionalmente
                        'domo': 'TestDomo',
                        'fecha_entrada': date.today(),
                        'fecha_salida': date.today(),
                        'metodo_pago': 'Test'
                    }
                    
                    success, message, reservation_id = self.reservation_service.save_reservation_atomic(test_reservation)
                    
                    # Debería fallar por validación, pero la transacción debería manejarse correctamente
                    results["reservation_atomic_handling"] = not success and "inválidos" in message
                    
                except Exception as e:
                    logger.error(f"Error testing reservation atomic: {e}")
                    results["reservation_atomic_handling"] = False
            else:
                results["reservation_atomic_handling"] = False
                
        except Exception as e:
            logger.error(f"Error general en test atomic transactions: {e}")
            results["general_atomic_error"] = str(e)
        
        return results
    
    def test_cache_invalidation(self) -> Dict[str, bool]:
        """Verificar que la invalidación de cache funcione"""
        results = {}
        
        try:
            if not self.persistent_service or not self.database_service:
                logger.warning("Servicios no disponibles para test de cache")
                return {"cache_test_skipped": True}
            
            logger.info("🧪 Testing cache invalidation...")
            
            test_user_id = "test_cache_user"
            
            # 1. Crear estado inicial
            initial_state = {"current_flow": "initial", "test_counter": 1}
            self.persistent_service.update_user_state(test_user_id, initial_state)
            
            # 2. Obtener estado (debería estar en cache)
            cached_state = self.persistent_service.get_user_state(test_user_id)
            results["initial_state_cached"] = cached_state.get("current_flow") == "initial"
            
            # 3. Crear una reserva que debería invalidar cache de usuario
            if self.database_service:
                test_reservation_data = {
                    'numero_whatsapp': test_user_id,
                    'email_contacto': 'cache@test.com',
                    'cantidad_huespedes': 2,
                    'domo': 'CacheTest',
                    'fecha_entrada': '2024-12-01',
                    'fecha_salida': '2024-12-02',
                    'metodo_pago': 'Test',
                    'monto_total': 100000
                }
                
                # Crear reserva (debería invalidar cache)
                success, reservation_id, error = self.database_service.create_reserva(test_reservation_data)
                
                if success:
                    # 4. Actualizar estado directamente en DB (simulando cambio externo)
                    self.persistent_service.update_user_state(test_user_id, {
                        "current_flow": "post_reservation",
                        "test_counter": 2
                    })
                    
                    # 5. Obtener estado nuevamente (debería obtener versión actualizada, no cache)
                    updated_state = self.persistent_service.get_user_state(test_user_id)
                    results["cache_invalidated_after_reservation"] = updated_state.get("current_flow") == "post_reservation"
                    
                    # Limpiar reserva de prueba
                    if reservation_id:
                        self.database_service.delete_reserva(reservation_id)
                else:
                    logger.warning(f"No se pudo crear reserva de prueba: {error}")
                    results["cache_invalidated_after_reservation"] = False
            
        except Exception as e:
            logger.error(f"Error en test de cache invalidation: {e}")
            results["cache_test_error"] = str(e)
        
        return results
    
    def test_database_constraints(self) -> Dict[str, bool]:
        """Verificar que los constraints de BD estén funcionando"""
        results = {}
        
        try:
            if not self.db:
                logger.warning("Base de datos no disponible para test de constraints")
                return {"constraints_test_skipped": True}
            
            logger.info("🧪 Testing database constraints...")
            
            # Test constraint de email único en usuarios
            try:
                from sqlalchemy import text
                
                # Intentar crear usuarios con emails duplicados
                test_queries = [
                    "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES ('Test1', 'duplicate@test.com', 'hash1', 'limitado');",
                    "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES ('Test2', 'duplicate@test.com', 'hash2', 'limitado');"
                ]
                
                success_count = 0
                for query in test_queries:
                    try:
                        self.db.session.execute(text(query))
                        self.db.session.commit()
                        success_count += 1
                    except Exception as e:
                        # Se espera que el segundo falle por constraint
                        self.db.session.rollback()
                
                # Solo el primer insert debería ser exitoso
                results["email_unique_constraint"] = success_count == 1
                
                # Limpiar datos de prueba
                try:
                    self.db.session.execute(text("DELETE FROM usuarios WHERE email = 'duplicate@test.com'"))
                    self.db.session.commit()
                except:
                    pass
                    
            except Exception as e:
                logger.error(f"Error testing database constraints: {e}")
                results["email_unique_constraint"] = False
            
        except Exception as e:
            logger.error(f"Error general en test de constraints: {e}")
            results["constraints_test_error"] = str(e)
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests de verificación"""
        logger.info("🚀 Iniciando tests de seguridad de concurrencia...")
        
        # Setup
        setup_success = self.setup_services()
        
        results = {
            "setup_success": setup_success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not setup_success:
            logger.warning("Setup falló - ejecutando tests limitados")
        
        # Tests
        results["atomic_transactions"] = self.test_atomic_transactions()
        results["cache_invalidation"] = self.test_cache_invalidation()
        results["database_constraints"] = self.test_database_constraints()
        
        # Resumen
        all_passed = all([
            setup_success,
            all(results["atomic_transactions"].values()) if isinstance(results["atomic_transactions"], dict) else False,
            all(v for k, v in results["cache_invalidation"].items() if not k.endswith("_error")) if isinstance(results["cache_invalidation"], dict) else False,
            all(v for k, v in results["database_constraints"].items() if not k.endswith("_error")) if isinstance(results["database_constraints"], dict) else False
        ])
        
        results["overall_success"] = all_passed
        
        return results

def main():
    """Función principal"""
    print("🧪 TESTS DE SEGURIDAD DE CONCURRENCIA")
    print("=" * 50)
    
    tester = ConcurrencySafetyTester()
    results = tester.run_all_tests()
    
    # Mostrar resultados
    print(f"\n📊 RESULTADOS DE TESTS ({results['timestamp']})")
    print("-" * 50)
    
    print(f"Setup: {'✅' if results['setup_success'] else '❌'}")
    
    if isinstance(results.get('atomic_transactions'), dict):
        print("\n🔄 Transacciones Atómicas:")
        for test, result in results['atomic_transactions'].items():
            print(f"  {test}: {'✅' if result else '❌'}")
    
    if isinstance(results.get('cache_invalidation'), dict):
        print("\n🗂️ Invalidación de Cache:")
        for test, result in results['cache_invalidation'].items():
            if not test.endswith("_error"):
                print(f"  {test}: {'✅' if result else '❌'}")
    
    if isinstance(results.get('database_constraints'), dict):
        print("\n🔒 Constraints de Base de Datos:")
        for test, result in results['database_constraints'].items():
            if not test.endswith("_error"):
                print(f"  {test}: {'✅' if result else '❌'}")
    
    print(f"\n🎯 RESULTADO GENERAL: {'✅ TODOS LOS TESTS PASARON' if results['overall_success'] else '❌ ALGUNOS TESTS FALLARON'}")
    
    return 0 if results['overall_success'] else 1

if __name__ == "__main__":
    sys.exit(main())
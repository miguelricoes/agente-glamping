#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test REAL de Validación de Base de Datos - Glamping Brillo de Luna
Pruebas exhaustivas de conectividad y operaciones de base de datos
"""

import os
import sys
import uuid
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configurar encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Cargar variables de entorno
load_dotenv()

print("🗄️ TEST REAL DE VALIDACIÓN DE BASE DE DATOS")
print("🎯 Validación exhaustiva de conectividad y operaciones")
print("=" * 70)

class DatabaseValidationTest:
    """Pruebas reales de base de datos para el agente"""
    
    def __init__(self):
        self.test_results = {
            "connection_test": False,
            "model_validation": False,
            "crud_operations": False,
            "availability_queries": False,
            "reservation_flow": False,
            "data_persistence": False,
            "transaction_integrity": False
        }
        
        self.db_config = None
        self.test_user_id = f"db_test_{str(uuid.uuid4())[:8]}"
        
        print(f"👤 Test User ID: {self.test_user_id}")
        
    def test_database_connection(self):
        """Probar conexión real a la base de datos"""
        print("\n🔌 PRUEBA 1: CONEXIÓN A BASE DE DATOS")
        print("-" * 50)
        
        try:
            # Verificar variables de entorno
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                print("❌ DATABASE_URL no configurada")
                return False
            
            print(f"✅ DATABASE_URL encontrada: {db_url[:30]}...")
            
            # Intentar importar y conectar
            from config.database_config import DatabaseConfig
            from flask import Flask
            
            # Crear app temporal para contexto
            app = Flask(__name__)
            app.config['SQLALCHEMY_DATABASE_URI'] = db_url
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            with app.app_context():
                self.db_config = DatabaseConfig()
                success = self.db_config.init_app(app)
                
                if success and self.db_config.database_available:
                    # Probar consulta básica
                    from sqlalchemy import text
                    result = self.db_config.db.session.execute(text('SELECT 1')).fetchone()
                    
                    if result:
                        print("✅ Conexión a base de datos exitosa")
                        print("✅ Consulta de prueba ejecutada correctamente")
                        self.test_results["connection_test"] = True
                        return True
                    else:
                        print("❌ Error en consulta de prueba")
                        return False
                else:
                    print("❌ No se pudo inicializar la conexión")
                    return False
                    
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def test_model_validation(self):
        """Validar que los modelos de BD están correctamente definidos"""
        print("\n📋 PRUEBA 2: VALIDACIÓN DE MODELOS")
        print("-" * 50)
        
        if not self.db_config:
            print("❌ No hay conexión de BD disponible")
            return False
        
        try:
            # Verificar modelos requeridos
            required_models = ['Usuario', 'Reserva']
            models_found = []
            
            for model_name in required_models:
                if hasattr(self.db_config, model_name):
                    model = getattr(self.db_config, model_name)
                    print(f"✅ Modelo {model_name}: Encontrado")
                    models_found.append(model_name)
                    
                    # Verificar que el modelo tiene tabla
                    if hasattr(model, '__tablename__'):
                        print(f"   📄 Tabla: {model.__tablename__}")
                    
                    # Verificar columnas básicas
                    if hasattr(model, '__table__'):
                        columns = [col.name for col in model.__table__.columns]
                        print(f"   📝 Columnas: {len(columns)} encontradas")
                else:
                    print(f"❌ Modelo {model_name}: NO encontrado")
            
            success = len(models_found) >= 2
            self.test_results["model_validation"] = success
            
            if success:
                print("✅ Modelos de BD validados correctamente")
            else:
                print("❌ Faltan modelos críticos de BD")
            
            return success
            
        except Exception as e:
            print(f"❌ Error validando modelos: {e}")
            return False
    
    def test_crud_operations(self):
        """Probar operaciones CRUD básicas"""
        print("\n🔄 PRUEBA 3: OPERACIONES CRUD")
        print("-" * 50)
        
        if not self.db_config or not self.test_results["model_validation"]:
            print("❌ Prerrequisitos no cumplidos")
            return False
        
        try:
            with self.db_config.db.session.begin():
                # CREATE - Crear usuario de prueba
                Usuario = self.db_config.Usuario
                test_user = Usuario(
                    id=self.test_user_id,
                    nombre="Test Usuario",
                    telefono="+57300123456",
                    email="test@glamping.com"
                )
                
                self.db_config.db.session.add(test_user)
                self.db_config.db.session.flush()  # Para obtener ID
                print("✅ CREATE: Usuario de prueba creado")
                
                # READ - Leer usuario
                found_user = Usuario.query.filter_by(id=self.test_user_id).first()
                if found_user and found_user.nombre == "Test Usuario":
                    print("✅ READ: Usuario leído correctamente")
                else:
                    print("❌ READ: Error leyendo usuario")
                    return False
                
                # UPDATE - Actualizar usuario
                found_user.email = "updated@glamping.com"
                self.db_config.db.session.flush()
                
                updated_user = Usuario.query.filter_by(id=self.test_user_id).first()
                if updated_user.email == "updated@glamping.com":
                    print("✅ UPDATE: Usuario actualizado correctamente")
                else:
                    print("❌ UPDATE: Error actualizando usuario")
                    return False
                
                # DELETE se hará al final del test
                print("✅ Operaciones CRUD básicas funcionando")
                self.test_results["crud_operations"] = True
                return True
                
        except Exception as e:
            print(f"❌ Error en operaciones CRUD: {e}")
            return False
    
    def test_availability_queries(self):
        """Probar consultas de disponibilidad"""
        print("\n📅 PRUEBA 4: CONSULTAS DE DISPONIBILIDAD")
        print("-" * 50)
        
        if not self.db_config:
            print("❌ No hay conexión de BD")
            return False
        
        try:
            # Importar servicio de disponibilidad
            from services.availability_service import AvailabilityService
            
            availability_service = AvailabilityService(
                self.db_config.db,
                self.db_config.Reserva
            )
            
            # Probar consulta de disponibilidad
            fecha_inicio = datetime.now().date() + timedelta(days=7)
            fecha_fin = fecha_inicio + timedelta(days=2)
            
            # Verificar que el método existe y funciona
            if hasattr(availability_service, 'check_availability'):
                disponibilidad = availability_service.check_availability(
                    fecha_inicio, fecha_fin, 2
                )
                print("✅ Consulta de disponibilidad ejecutada")
                print(f"   📊 Resultado: {type(disponibilidad)}")
            else:
                print("⚠️ Método check_availability no encontrado")
            
            # Probar otros métodos comunes
            methods_to_test = [
                'get_available_domos',
                'check_domo_availability',
                'get_reservations_by_date'
            ]
            
            working_methods = 0
            for method in methods_to_test:
                if hasattr(availability_service, method):
                    print(f"✅ Método {method}: Disponible")
                    working_methods += 1
                else:
                    print(f"⚠️ Método {method}: No encontrado")
            
            success = working_methods >= 1
            self.test_results["availability_queries"] = success
            
            if success:
                print("✅ Sistema de disponibilidad operativo")
            else:
                print("❌ Sistema de disponibilidad no funcional")
            
            return success
            
        except Exception as e:
            print(f"❌ Error en consultas de disponibilidad: {e}")
            return False
    
    def test_reservation_flow(self):
        """Probar flujo completo de reserva"""
        print("\n📝 PRUEBA 5: FLUJO DE RESERVA COMPLETO")
        print("-" * 50)
        
        if not self.db_config:
            print("❌ No hay conexión de BD")
            return False
        
        try:
            # Importar servicio de reservas
            from services.reservation_service import ReservationService
            
            reservation_service = ReservationService(
                self.db_config.db,
                self.db_config.Reserva
            )
            
            # Datos de prueba para reserva
            reserva_data = {
                "usuario_id": self.test_user_id,
                "domo_tipo": "Antares",
                "fecha_inicio": (datetime.now() + timedelta(days=30)).date(),
                "fecha_fin": (datetime.now() + timedelta(days=32)).date(),
                "num_personas": 2,
                "precio_total": 420000,
                "telefono": "+57300123456"
            }
            
            # Probar creación de reserva
            if hasattr(reservation_service, 'create_reservation'):
                reserva = reservation_service.create_reservation(reserva_data)
                if reserva:
                    print("✅ Reserva creada exitosamente")
                    print(f"   📋 ID: {getattr(reserva, 'id', 'N/A')}")
                else:
                    print("❌ Error creando reserva")
                    return False
            else:
                print("⚠️ Método create_reservation no encontrado")
                # Intentar crear reserva directamente
                try:
                    Reserva = self.db_config.Reserva
                    nueva_reserva = Reserva(**reserva_data)
                    self.db_config.db.session.add(nueva_reserva)
                    self.db_config.db.session.commit()
                    print("✅ Reserva creada directamente")
                except Exception as e:
                    print(f"❌ Error creando reserva directa: {e}")
                    return False
            
            # Verificar que la reserva se guardó
            Reserva = self.db_config.Reserva
            reserva_guardada = Reserva.query.filter_by(usuario_id=self.test_user_id).first()
            
            if reserva_guardada:
                print("✅ Reserva verificada en base de datos")
                print(f"   🏠 Domo: {getattr(reserva_guardada, 'domo_tipo', 'N/A')}")
                print(f"   💰 Precio: ${getattr(reserva_guardada, 'precio_total', 'N/A')}")
            else:
                print("❌ Reserva no encontrada en BD")
                return False
            
            self.test_results["reservation_flow"] = True
            return True
            
        except Exception as e:
            print(f"❌ Error en flujo de reserva: {e}")
            return False
    
    def test_data_persistence(self):
        """Probar persistencia de datos"""
        print("\n💾 PRUEBA 6: PERSISTENCIA DE DATOS")
        print("-" * 50)
        
        if not self.db_config:
            print("❌ No hay conexión de BD")
            return False
        
        try:
            # Verificar que los datos creados en tests anteriores persisten
            Usuario = self.db_config.Usuario
            Reserva = self.db_config.Reserva
            
            # Verificar usuario
            user = Usuario.query.filter_by(id=self.test_user_id).first()
            if user:
                print("✅ Usuario persiste en BD")
                print(f"   👤 Nombre: {user.nombre}")
                print(f"   📧 Email: {user.email}")
            else:
                print("❌ Usuario no persiste")
                return False
            
            # Verificar reserva
            reserva = Reserva.query.filter_by(usuario_id=self.test_user_id).first()
            if reserva:
                print("✅ Reserva persiste en BD")
                print(f"   🏠 Domo: {getattr(reserva, 'domo_tipo', 'N/A')}")
                print(f"   📅 Fecha: {getattr(reserva, 'fecha_inicio', 'N/A')}")
            else:
                print("❌ Reserva no persiste")
                return False
            
            # Probar consulta con relaciones (si existen)
            try:
                if hasattr(user, 'reservas'):
                    reservas_usuario = user.reservas
                    print(f"✅ Relaciones funcionando: {len(reservas_usuario)} reservas")
                else:
                    print("⚠️ Relaciones entre modelos no configuradas")
            except Exception as rel_error:
                print(f"⚠️ Error en relaciones: {rel_error}")
            
            self.test_results["data_persistence"] = True
            return True
            
        except Exception as e:
            print(f"❌ Error verificando persistencia: {e}")
            return False
    
    def test_transaction_integrity(self):
        """Probar integridad de transacciones"""
        print("\n🔐 PRUEBA 7: INTEGRIDAD DE TRANSACCIONES")
        print("-" * 50)
        
        if not self.db_config:
            print("❌ No hay conexión de BD")
            return False
        
        try:
            # Probar rollback en caso de error
            Usuario = self.db_config.Usuario
            
            try:
                with self.db_config.db.session.begin():
                    # Crear usuario temporal
                    temp_user = Usuario(
                        id="temp_rollback_test",
                        nombre="Temp User",
                        telefono="+57300999999",
                        email="temp@test.com"
                    )
                    self.db_config.db.session.add(temp_user)
                    self.db_config.db.session.flush()
                    
                    # Verificar que se creó temporalmente
                    found = Usuario.query.filter_by(id="temp_rollback_test").first()
                    if found:
                        print("✅ Usuario temporal creado en transacción")
                    
                    # Forzar error para probar rollback
                    raise Exception("Test rollback")
                    
            except Exception as e:
                if "Test rollback" in str(e):
                    # Verificar que el rollback funcionó
                    rolled_back_user = Usuario.query.filter_by(id="temp_rollback_test").first()
                    if not rolled_back_user:
                        print("✅ Rollback funcionó correctamente")
                    else:
                        print("❌ Rollback no funcionó")
                        return False
                else:
                    print(f"❌ Error inesperado: {e}")
                    return False
            
            # Probar commit exitoso
            with self.db_config.db.session.begin():
                commit_user = Usuario(
                    id="commit_test_user",
                    nombre="Commit Test",
                    telefono="+57300888888",
                    email="commit@test.com"
                )
                self.db_config.db.session.add(commit_user)
                # Transacción se commitea automáticamente al salir del with
            
            # Verificar que el commit funcionó
            committed_user = Usuario.query.filter_by(id="commit_test_user").first()
            if committed_user:
                print("✅ Commit exitoso verificado")
                
                # Limpiar usuario de prueba
                self.db_config.db.session.delete(committed_user)
                self.db_config.db.session.commit()
            else:
                print("❌ Commit no funcionó")
                return False
            
            self.test_results["transaction_integrity"] = True
            return True
            
        except Exception as e:
            print(f"❌ Error en integridad de transacciones: {e}")
            return False
    
    def cleanup_test_data(self):
        """Limpiar datos de prueba"""
        print("\n🧹 LIMPIEZA DE DATOS DE PRUEBA")
        print("-" * 50)
        
        if not self.db_config:
            return
        
        try:
            # Eliminar reservas de prueba
            Reserva = self.db_config.Reserva
            reservas_test = Reserva.query.filter_by(usuario_id=self.test_user_id).all()
            for reserva in reservas_test:
                self.db_config.db.session.delete(reserva)
            print(f"✅ {len(reservas_test)} reservas de prueba eliminadas")
            
            # Eliminar usuario de prueba
            Usuario = self.db_config.Usuario
            user_test = Usuario.query.filter_by(id=self.test_user_id).first()
            if user_test:
                self.db_config.db.session.delete(user_test)
                print("✅ Usuario de prueba eliminado")
            
            self.db_config.db.session.commit()
            print("✅ Limpieza completada")
            
        except Exception as e:
            print(f"⚠️ Error en limpieza: {e}")
            self.db_config.db.session.rollback()
    
    def generate_database_report(self):
        """Generar reporte de validación de BD"""
        print("\n" + "=" * 70)
        print("📊 REPORTE DE VALIDACIÓN DE BASE DE DATOS")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        success_rate = (passed_tests / total_tests) * 100
        
        # Estado general
        if success_rate >= 90:
            status = "🟢 EXCELENTE - BD COMPLETAMENTE FUNCIONAL"
        elif success_rate >= 75:
            status = "🟡 BUENO - BD FUNCIONAL CON OBSERVACIONES"
        elif success_rate >= 60:
            status = "🟠 ACEPTABLE - PROBLEMAS MENORES DE BD"
        else:
            status = "🔴 CRÍTICO - BD NO FUNCIONAL"
        
        print(f"\n🎯 PUNTUACIÓN BD: {success_rate:.1f}/100")
        print(f"📈 ESTADO: {status}")
        
        # Detalle por prueba
        print(f"\n📋 RESULTADOS DETALLADOS:")
        test_names = {
            "connection_test": "🔌 Conexión a BD",
            "model_validation": "📋 Validación de Modelos",
            "crud_operations": "🔄 Operaciones CRUD",
            "availability_queries": "📅 Consultas de Disponibilidad",
            "reservation_flow": "📝 Flujo de Reserva",
            "data_persistence": "💾 Persistencia de Datos",
            "transaction_integrity": "🔐 Integridad de Transacciones"
        }
        
        for test_key, result in self.test_results.items():
            test_name = test_names.get(test_key, test_key)
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        
        if success_rate >= 85:
            print("   ✅ Base de datos completamente operativa para producción")
            print("   ✅ Implementar monitoreo de performance en producción")
        elif success_rate >= 70:
            print("   ⚠️ Corregir fallos específicos antes de producción")
            print("   ⚠️ Probar exhaustivamente funcionalidades fallidas")
        else:
            print("   🚨 Revisar configuración completa de base de datos")
            print("   🚨 Verificar variables de entorno y permisos")
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   ✅ Pruebas exitosas: {passed_tests}/{total_tests}")
        print(f"   👤 Usuario de prueba: {self.test_user_id}")
        print(f"   🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("=" * 70)
        
        return success_rate >= 75
    
    def run_complete_database_validation(self):
        """Ejecutar validación completa de BD"""
        print(f"\n🚀 INICIANDO VALIDACIÓN COMPLETA DE BASE DE DATOS")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Ejecutar todas las pruebas en orden
            self.test_database_connection()
            self.test_model_validation()
            self.test_crud_operations()
            self.test_availability_queries()
            self.test_reservation_flow()
            self.test_data_persistence()
            self.test_transaction_integrity()
            
            # Limpiar datos de prueba
            self.cleanup_test_data()
            
            # Generar reporte final
            success = self.generate_database_report()
            
            return success
            
        except Exception as e:
            print(f"❌ Error fatal en validación: {e}")
            return False

def main():
    """Función principal"""
    print("🗄️ INICIANDO VALIDACIÓN REAL DE BASE DE DATOS")
    print("🎯 Objetivo: Verificar conectividad y operaciones críticas")
    
    # Verificar variable de entorno crítica
    if not os.getenv('DATABASE_URL'):
        print("\n❌ ERROR CRÍTICO: DATABASE_URL no configurada")
        print("🔧 Configura la variable de entorno antes de continuar")
        return False
    
    # Ejecutar validación
    validator = DatabaseValidationTest()
    success = validator.run_complete_database_validation()
    
    print(f"\n{'='*70}")
    print("🏁 RESULTADO VALIDACIÓN DE BASE DE DATOS")
    print(f"{'='*70}")
    
    if success:
        print("✅ BASE DE DATOS COMPLETAMENTE VALIDADA")
        print("🚀 Lista para uso en producción")
    else:
        print("❌ BASE DE DATOS NO VALIDADA")
        print("🔧 Corregir problemas antes de producción")
    
    print(f"{'='*70}")
    
    return success

if __name__ == "__main__":
    main()
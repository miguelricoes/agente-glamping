# Test del servicio centralizado de validación
# Verifica funcionalidad de ValidationService

import sys
import os
from datetime import date, timedelta
from unittest.mock import Mock, patch

# Agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar encoding para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

def test_validate_guest_names():
    """Test de validación de nombres de huéspedes"""
    
    print("=== TEST: Validate Guest Names ===")
    
    try:
        from services.validation_service import ValidationService
        
        service = ValidationService()
        
        # Test casos válidos
        test_cases = [
            ("Juan Pérez", True, 1, "Nombre simple"),
            ("Ana María, Carlos José", True, 2, "Dos nombres con coma"),
            (["Pedro", "María", "Luis"], True, 3, "Lista de nombres"),
            ("José\nMaría\nCarlos", True, 3, "Nombres con saltos de línea"),
            ("  Ana   ,   Carlos  ", True, 2, "Nombres con espacios extras")
        ]
        
        for names_input, expected_valid, expected_count, description in test_cases:
            success, nombres, error = service.validate_guest_names(names_input)
            
            print(f"✓ Test: {description}")
            print(f"  - Input: {names_input}")
            print(f"  - Válido: {success} (esperado: {expected_valid})")
            print(f"  - Cantidad: {len(nombres) if nombres else 0} (esperado: {expected_count})")
            
            if success == expected_valid and len(nombres) == expected_count:
                print(f"  ✓ PASÓ")
            else:
                print(f"  ✗ FALLÓ")
                return False
        
        # Test casos inválidos
        invalid_cases = [
            ("", "Nombres vacíos"),
            ("X", "Nombre muy corto"),
            ("A" * 60, "Nombre muy largo"),
            (None, "Input None")
        ]
        
        for invalid_input, description in invalid_cases:
            success, nombres, error = service.validate_guest_names(invalid_input)
            
            print(f"✓ Test inválido: {description}")
            print(f"  - Input: {invalid_input}")
            print(f"  - Válido: {success} (esperado: False)")
            print(f"  - Error: {error}")
            
            if not success:
                print(f"  ✓ PASÓ - Error detectado correctamente")
            else:
                print(f"  ✗ FALLÓ - Debería haber detectado error")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test validate guest names: {e}")
        return False

def test_parse_flexible_date():
    """Test de parsing flexible de fechas"""
    
    print("\n=== TEST: Parse Flexible Date ===")
    
    try:
        from services.validation_service import ValidationService
        
        service = ValidationService()
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Test casos válidos
        valid_cases = [
            (tomorrow.strftime("%Y-%m-%d"), "Formato ISO"),
            (tomorrow.strftime("%d/%m/%Y"), "Formato DD/MM/YYYY"), 
            (tomorrow.strftime("%d-%m-%Y"), "Formato DD-MM-YYYY"),
            (tomorrow.strftime("%d.%m.%Y"), "Formato DD.MM.YYYY")
        ]
        
        for date_str, description in valid_cases:
            success, parsed_date, error = service.parse_flexible_date(date_str)
            
            print(f"✓ Test: {description}")
            print(f"  - Input: {date_str}")
            print(f"  - Válido: {success}")
            print(f"  - Fecha: {parsed_date}")
            
            if success and parsed_date:
                print(f"  ✓ PASÓ")
            else:
                print(f"  ✗ FALLÓ - Error: {error}")
                return False
        
        # Test casos inválidos
        invalid_cases = [
            ("", "Fecha vacía"),
            ("not-a-date", "Texto inválido"),
            ("32/13/2024", "Fecha imposible"),
            ((today - timedelta(days=2)).strftime("%Y-%m-%d"), "Fecha pasada")
        ]
        
        for date_str, description in invalid_cases:
            success, parsed_date, error = service.parse_flexible_date(date_str)
            
            print(f"✓ Test inválido: {description}")
            print(f"  - Input: {date_str}")
            print(f"  - Válido: {success} (esperado: False)")
            print(f"  - Error: {error}")
            
            if not success:
                print(f"  ✓ PASÓ - Error detectado correctamente")
            else:
                print(f"  ✗ FALLÓ - Debería haber detectado error")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test parse flexible date: {e}")
        return False

def test_validate_contact_info():
    """Test de validación de información de contacto"""
    
    print("\n=== TEST: Validate Contact Info ===")
    
    try:
        from services.validation_service import ValidationService
        
        service = ValidationService()
        
        # Test casos válidos
        valid_cases = [
            ("+573001234567", "user@example.com", "Formato completo"),
            ("3001234567", "test@gmail.com", "Número sin código país"),
            ("573001234567", "admin@company.co", "Con código país sin +")
        ]
        
        for phone, email, description in valid_cases:
            success, phone_clean, email_clean, errors = service.validate_contact_info(phone, email)
            
            print(f"✓ Test: {description}")
            print(f"  - Phone: {phone} → {phone_clean}")
            print(f"  - Email: {email} → {email_clean}")
            print(f"  - Válido: {success}")
            print(f"  - Errores: {errors}")
            
            if success and not errors:
                print(f"  ✓ PASÓ")
            else:
                print(f"  ✗ FALLÓ - Errores inesperados")
                return False
        
        # Test casos inválidos
        invalid_cases = [
            ("123", "invalid-email", "Phone y email inválidos"),
            ("", "", "Campos vacíos"),
            ("+57300", "user@", "Formatos incorrectos")
        ]
        
        for phone, email, description in invalid_cases:
            success, phone_clean, email_clean, errors = service.validate_contact_info(phone, email)
            
            print(f"✓ Test inválido: {description}")
            print(f"  - Phone: {phone}")
            print(f"  - Email: {email}")
            print(f"  - Válido: {success} (esperado: False)")
            print(f"  - Errores: {len(errors)} errores")
            
            if not success and errors:
                print(f"  ✓ PASÓ - Errores detectados correctamente")
            else:
                print(f"  ✗ FALLÓ - Debería haber detectado errores")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test validate contact info: {e}")
        return False

def test_validate_domo_selection():
    """Test de validación de selección de domo"""
    
    print("\n=== TEST: Validate Domo Selection ===")
    
    try:
        from services.validation_service import ValidationService
        
        service = ValidationService()
        
        # Test casos válidos
        valid_cases = [
            ("antares", "Antares", "Minúscula"),
            ("POLARIS", "Polaris", "Mayúscula"), 
            ("Sirius", "Sirius", "Capitalizado"),
            ("centauro", "Centaury", "Alias centauro"),
            ("  antares  ", "Antares", "Con espacios")
        ]
        
        for input_domo, expected_domo, description in valid_cases:
            success, domo_clean, error = service.validate_domo_selection(input_domo)
            
            print(f"✓ Test: {description}")
            print(f"  - Input: '{input_domo}' → '{domo_clean}'")
            print(f"  - Válido: {success}")
            print(f"  - Esperado: {expected_domo}")
            
            if success and domo_clean == expected_domo:
                print(f"  ✓ PASÓ")
            else:
                print(f"  ✗ FALLÓ - Error: {error}")
                return False
        
        # Test casos inválidos
        invalid_cases = [
            ("", "Domo vacío"),
            ("luna", "Domo inexistente"),
            ("xyz", "Nombre inválido")
        ]
        
        for input_domo, description in invalid_cases:
            success, domo_clean, error = service.validate_domo_selection(input_domo)
            
            print(f"✓ Test inválido: {description}")
            print(f"  - Input: '{input_domo}'")
            print(f"  - Válido: {success} (esperado: False)")
            print(f"  - Error: {error}")
            
            if not success:
                print(f"  ✓ PASÓ - Error detectado correctamente")
            else:
                print(f"  ✗ FALLÓ - Debería haber detectado error")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test validate domo selection: {e}")
        return False

def test_validate_guest_count():
    """Test de validación de cantidad de huéspedes"""
    
    print("\n=== TEST: Validate Guest Count ===")
    
    try:
        from services.validation_service import ValidationService
        
        service = ValidationService()
        
        # Test casos válidos
        valid_cases = [
            (1, "Un huésped"),
            (2, "Dos huéspedes"),
            ("4", "String número"),
            (10, "Máximo permitido")
        ]
        
        for input_count, description in valid_cases:
            success, count_clean, error = service.validate_guest_count(input_count)
            
            print(f"✓ Test: {description}")
            print(f"  - Input: {input_count} → {count_clean}")
            print(f"  - Válido: {success}")
            
            if success and count_clean > 0:
                print(f"  ✓ PASÓ")
            else:
                print(f"  ✗ FALLÓ - Error: {error}")
                return False
        
        # Test casos inválidos
        invalid_cases = [
            (0, "Cero huéspedes"),
            (-1, "Número negativo"),
            (15, "Más del máximo"),
            ("abc", "Texto inválido"),
            (None, "Valor None")
        ]
        
        for input_count, description in invalid_cases:
            success, count_clean, error = service.validate_guest_count(input_count)
            
            print(f"✓ Test inválido: {description}")
            print(f"  - Input: {input_count}")
            print(f"  - Válido: {success} (esperado: False)")
            print(f"  - Error: {error}")
            
            if not success:
                print(f"  ✓ PASÓ - Error detectado correctamente")
            else:
                print(f"  ✗ FALLÓ - Debería haber detectado error")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test validate guest count: {e}")
        return False

def test_validate_campos_importantes_reserva():
    """Test de validación de campos importantes de reserva"""
    
    print("\n=== TEST: Validate Campos Importantes Reserva ===")
    
    try:
        from services.validation_service import ValidationService
        
        service = ValidationService()
        tomorrow = date.today() + timedelta(days=1)
        day_after = date.today() + timedelta(days=2)
        
        # Test caso válido completo
        valid_data = {
            'numero_whatsapp': '+573001234567',
            'email_contacto': 'user@example.com',
            'cantidad_huespedes': 2,
            'domo': 'antares',
            'fecha_entrada': tomorrow,
            'fecha_salida': day_after,
            'metodo_pago': 'tarjeta'
        }
        
        success, errors = service.validate_campos_importantes_reserva(valid_data)
        
        print("✓ Test datos válidos completos:")
        print(f"  - Válido: {success}")
        print(f"  - Errores: {errors}")
        
        if success and not errors:
            print("  ✓ PASÓ")
        else:
            print("  ✗ FALLÓ - Errores inesperados en datos válidos")
            return False
        
        # Test campos faltantes
        incomplete_data = {
            'numero_whatsapp': '+573001234567',
            'email_contacto': 'user@example.com'
            # Faltan otros campos requeridos
        }
        
        success, errors = service.validate_campos_importantes_reserva(incomplete_data)
        
        print("\n✓ Test datos incompletos:")
        print(f"  - Válido: {success} (esperado: False)")
        print(f"  - Errores: {len(errors)} errores detectados")
        
        if not success and len(errors) > 0:
            print("  ✓ PASÓ - Campos faltantes detectados")
        else:
            print("  ✗ FALLÓ - Debería detectar campos faltantes")
            return False
        
        # Test datos inválidos
        invalid_data = {
            'numero_whatsapp': '123',  # Muy corto
            'email_contacto': 'invalid-email',  # Formato inválido
            'cantidad_huespedes': 0,  # Cero huéspedes
            'domo': 'inexistente',  # Domo no válido
            'fecha_entrada': tomorrow,
            'fecha_salida': tomorrow,  # Misma fecha (inválido)
            'metodo_pago': 'cryptocurrency'  # Método no válido
        }
        
        success, errors = service.validate_campos_importantes_reserva(invalid_data)
        
        print("\n✓ Test datos inválidos:")
        print(f"  - Válido: {success} (esperado: False)")
        print(f"  - Errores: {len(errors)} errores detectados")
        
        if not success and len(errors) > 0:
            print("  ✓ PASÓ - Errores de validación detectados")
        else:
            print("  ✗ FALLÓ - Debería detectar errores de validación")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error en test validate campos importantes reserva: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests del servicio de validación"""
    
    print("INICIANDO TESTS DEL SERVICIO DE VALIDACIÓN")
    print("=" * 60)
    
    tests = [
        test_validate_guest_names,
        test_parse_flexible_date,
        test_validate_contact_info,
        test_validate_domo_selection,
        test_validate_guest_count,
        test_validate_campos_importantes_reserva
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Error inesperado en {test_func.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    print(f"Tests pasados: {passed}/{total}")
    print(f"Porcentaje de éxito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✅ TODOS LOS TESTS PASARON")
        print("\nValidationService listo para usar:")
        print("• Validación de nombres de huéspedes")
        print("• Parsing flexible de fechas")
        print("• Validación de información de contacto")
        print("• Validación de selección de domos")
        print("• Validación de cantidad de huéspedes")
        print("• Validación completa de campos de reserva")
        print("• Parsing seguro de respuestas JSON de LLM")
        print("• Logging estructurado integrado")
        return True
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
# Testing incremental para verificar que el refactoring no rompe nada
# Este archivo contiene tests básicos para validar la funcionalidad

import sys
import traceback
from datetime import datetime, date

def test_imports():
    """Test 1: Verificar que todos los módulos se pueden importar"""
    print("=== TEST 1: IMPORTS ===")
    
    tests = [
        ("agente original", "import agente"),
        ("agente modular", "import agente_modular"),
        ("whatsapp routes", "from routes.whatsapp_routes import register_whatsapp_routes"),
        ("chat routes", "from routes.chat_routes import register_chat_routes"),
        ("conversation service", "from services.conversation_service import *"),
        ("validators", "from utils.validators import *"),
        ("conversation state", "from models.conversation_state import ConversationState")
    ]
    
    results = []
    for name, import_cmd in tests:
        try:
            exec(import_cmd)
            print(f"✓ {name}: OK")
            results.append((name, True, None))
        except Exception as e:
            print(f"✗ {name}: ERROR - {e}")
            results.append((name, False, str(e)))
    
    return results

def test_validators():
    """Test 2: Verificar funcionalidad de validators"""
    print("\n=== TEST 2: VALIDATORS ===")
    
    try:
        from utils.validators import (
            validate_guest_names, parse_flexible_date, validate_date_range,
            validate_contact_info, validate_domo_selection
        )
        
        tests = []
        
        # Test guest names
        success, names, msg = validate_guest_names("Juan Pérez, María González")
        tests.append(("Guest names validation", success and len(names) == 2))
        print(f"✓ Guest names: {success}, Names: {names}")
        
        # Test contact info
        success, phone, email, errors = validate_contact_info("3001234567", "test@example.com")
        tests.append(("Contact validation", success and len(errors) == 0))
        print(f"✓ Contact info: {success}, Phone: {phone}, Email: {email}")
        
        # Test domo selection
        success, domo, msg = validate_domo_selection("antares")
        tests.append(("Domo selection", success and domo == "Antares"))
        print(f"✓ Domo selection: {success}, Domo: {domo}")
        
        return tests
        
    except Exception as e:
        print(f"✗ Validators test failed: {e}")
        return [("Validators", False)]

def test_conversation_service():
    """Test 3: Verificar funcionalidad del servicio de conversación"""
    print("\n=== TEST 3: CONVERSATION SERVICE ===")
    
    try:
        from services.conversation_service import (
            add_message_to_memory, is_new_conversation, detect_reservation_intent,
            messages_to_dict
        )
        
        tests = []
        
        # Test reservation intent detection
        result1 = detect_reservation_intent("quiero hacer una reserva")
        result2 = detect_reservation_intent("hola como estas")
        tests.append(("Reservation intent detection", result1 and not result2))
        print(f"✓ Reservation intent: 'quiero hacer una reserva' = {result1}")
        print(f"✓ Reservation intent: 'hola como estas' = {result2}")
        
        # Test messages to dict conversion
        mock_messages = [type('MockMessage', (), {'type': 'human', 'content': 'test'})()]
        result = messages_to_dict(mock_messages)
        tests.append(("Messages to dict", isinstance(result, list)))
        print(f"✓ Messages to dict: {type(result)} with {len(result)} items")
        
        return tests
        
    except Exception as e:
        print(f"✗ Conversation service test failed: {e}")
        traceback.print_exc()
        return [("Conversation service", False)]

def test_conversation_state():
    """Test 4: Verificar funcionalidad del estado de conversación"""
    print("\n=== TEST 4: CONVERSATION STATE ===")
    
    try:
        from models.conversation_state import ConversationState
        
        # Create conversation state
        state = ConversationState("test_user")
        state.current_flow = "reserva"
        state.step = 1
        
        # Test to_dict conversion
        state_dict = state.to_dict()
        tests = [
            ("State creation", state.user_id == "test_user"),
            ("State to dict", isinstance(state_dict, dict) and "current_flow" in state_dict),
            ("State from dict", ConversationState.from_dict("test2", state_dict).current_flow == "reserva")
        ]
        
        for name, result in tests:
            print(f"✓ {name}: {result}")
        
        return tests
        
    except Exception as e:
        print(f"✗ Conversation state test failed: {e}")
        return [("Conversation state", False)]

def test_system_initialization():
    """Test 5: Verificar que el sistema se inicializa correctamente"""
    print("\n=== TEST 5: SYSTEM INITIALIZATION ===")
    
    try:
        # Test that we can import without triggering full initialization
        import agente
        
        # Check critical components exist
        tests = [
            ("RAG chains exist", hasattr(agente, 'qa_chains')),
            ("User memories exist", hasattr(agente, 'user_memories')),
            ("User states exist", hasattr(agente, 'user_states')),
            ("Tools exist", hasattr(agente, 'tools')),
            ("Flask app exists", hasattr(agente, 'app'))
        ]
        
        for name, result in tests:
            print(f"✓ {name}: {result}")
        
        return tests
        
    except Exception as e:
        print(f"✗ System initialization test failed: {e}")
        return [("System initialization", False)]

def run_all_tests():
    """Ejecutar todos los tests y generar reporte"""
    print("INICIANDO TESTING INCREMENTAL")
    print("=" * 50)
    
    all_results = []
    
    # Ejecutar tests
    all_results.extend(test_imports())
    all_results.extend(test_validators())
    all_results.extend(test_conversation_service())
    all_results.extend(test_conversation_state())
    all_results.extend(test_system_initialization())
    
    # Generar reporte final
    print("\n" + "=" * 50)
    print("REPORTE FINAL DE TESTING")
    print("=" * 50)
    
    passed = sum(1 for _, success, _ in all_results if success)
    total = len(all_results)
    
    print(f"Tests pasados: {passed}/{total}")
    print(f"Porcentaje de exito: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("TODOS LOS TESTS PASARON")
        return True
    else:
        print("ALGUNOS TESTS FALLARON:")
        for name, success, error in all_results:
            if not success:
                print(f"  - {name}: {error}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
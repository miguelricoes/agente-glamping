#!/usr/bin/env python3
"""
Test para verificar si AdminContactService intercepta consultas de servicios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.admin_contact_service import get_admin_contact_service

def test_admin_interception():
    """Test si AdminContactService intercepta consultas de servicios"""
    
    admin_service = get_admin_contact_service()
    
    consultas_servicios = [
        "que servicios incluyen",
        "servicios incluidos", 
        "que servicios tienen",
        "servicios disponibles",
        "cuales son los servicios",
        "informacion sobre servicios"
    ]
    
    print("TESTING INTERCEPTACIÓN POR ADMINCONTACTSERVICE")
    print("=" * 60)
    
    for consulta in consultas_servicios:
        print(f"\nTEST: '{consulta}'")
        
        should_share, trigger_type, reason = admin_service.should_share_admin_contact(consulta)
        
        if should_share:
            print(f"❌ INTERCEPTADO: {trigger_type} - {reason}")
            print("   PROBLEMA: AdminContactService bloquea consultas de servicios")
        else:
            print("✅ NO INTERCEPTADO - Consulta puede pasar al fallback")

if __name__ == "__main__":
    test_admin_interception()
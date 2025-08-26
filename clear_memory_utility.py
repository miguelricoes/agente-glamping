#!/usr/bin/env python3
"""
Utilidad para limpiar completamente la memoria conversacional de un usuario
Elimina todos los datos de estado y memoria para empezar fresh
"""

import os
import json
import shutil
from typing import Optional
import sys
sys.path.append('.')

# Importar servicios del proyecto
from services.persistent_state_service import PersistentStateService
from models.conversation_state_db import ConversationStateDB
from models.database import init_db

def clear_user_memory(user_id: str, confirmation: bool = False) -> dict:
    """
    Limpiar completamente la memoria de un usuario específico
    
    Args:
        user_id: ID del usuario (ej: whatsapp573001234567, número de teléfono, etc)
        confirmation: True para confirmar la eliminación
    
    Returns:
        dict con el resultado de la operación
    """
    if not confirmation:
        return {
            "error": "Se requiere confirmation=True para confirmar la eliminación",
            "found_data": scan_user_data(user_id)
        }
    
    results = {
        "user_id": user_id,
        "cleared": {
            "memory_files": 0,
            "database_state": False,
            "database_memory": False
        },
        "errors": []
    }
    
    print(f"🗑️  LIMPIANDO MEMORIA PARA: {user_id}")
    
    # 1. Limpiar archivos de memoria en user_memories_data/
    memory_dir = "user_memories_data"
    if os.path.exists(memory_dir):
        files_to_delete = []
        
        # Buscar archivos que contengan el user_id
        for filename in os.listdir(memory_dir):
            if user_id in filename or filename.startswith(user_id):
                files_to_delete.append(filename)
        
        # También buscar por patrones comunes de WhatsApp
        if "whatsapp" in user_id.lower():
            phone_number = user_id.replace("whatsapp", "").replace("+", "")
            for filename in os.listdir(memory_dir):
                if phone_number in filename:
                    files_to_delete.append(filename)
        
        # Eliminar archivos encontrados
        for filename in files_to_delete:
            file_path = os.path.join(memory_dir, filename)
            try:
                os.remove(file_path)
                results["cleared"]["memory_files"] += 1
                print(f"  ✓ Eliminado: {filename}")
            except Exception as e:
                results["errors"].append(f"Error eliminando {filename}: {e}")
                print(f"  ❌ Error eliminando {filename}: {e}")
    
    # 2. Limpiar estado de base de datos si es posible
    try:
        # Intentar inicializar conexión a BD
        db = init_db()
        if db:
            state_db = ConversationStateDB(db)
            
            # Buscar el usuario en la base de datos
            user_state = state_db.UserConversationState.query.filter_by(user_id=user_id).first()
            
            if user_state:
                # Eliminar completamente el registro
                db.session.delete(user_state)
                db.session.commit()
                results["cleared"]["database_state"] = True
                results["cleared"]["database_memory"] = True
                print(f"  ✓ Estado y memoria eliminados de la base de datos")
            else:
                print(f"  ℹ️  Usuario no encontrado en base de datos")
                
    except Exception as e:
        results["errors"].append(f"Error con base de datos: {e}")
        print(f"  ❌ Error con base de datos: {e}")
    
    # 3. Limpiar directorio memory/ si existe
    memory_base_dir = "memory"
    if os.path.exists(memory_base_dir):
        user_memory_file = os.path.join(memory_base_dir, f"{user_id}.json")
        if os.path.exists(user_memory_file):
            try:
                os.remove(user_memory_file)
                results["cleared"]["memory_files"] += 1
                print(f"  ✓ Eliminado: memory/{user_id}.json")
            except Exception as e:
                results["errors"].append(f"Error eliminando memory/{user_id}.json: {e}")
    
    # Resumen
    total_cleared = results["cleared"]["memory_files"]
    if results["cleared"]["database_state"]:
        total_cleared += 1
    
    if total_cleared > 0:
        print(f"✅ MEMORIA LIMPIADA - {total_cleared} elementos eliminados")
    else:
        print(f"ℹ️  No se encontraron datos para limpiar")
    
    if results["errors"]:
        print(f"⚠️  {len(results['errors'])} errores ocurrieron")
    
    return results

def scan_user_data(user_id: str) -> dict:
    """
    Escanear qué datos existen para un usuario sin eliminarlos
    
    Args:
        user_id: ID del usuario a escanear
    
    Returns:
        dict con información de los datos encontrados
    """
    found = {
        "memory_files": [],
        "database_exists": False,
        "database_stats": {},
        "total_files": 0
    }
    
    # Escanear archivos de memoria
    memory_dir = "user_memories_data"
    if os.path.exists(memory_dir):
        for filename in os.listdir(memory_dir):
            if user_id in filename or filename.startswith(user_id):
                file_path = os.path.join(memory_dir, filename)
                file_size = os.path.getsize(file_path)
                found["memory_files"].append({
                    "filename": filename,
                    "size_bytes": file_size,
                    "path": file_path
                })
                found["total_files"] += 1
        
        # También buscar por números de teléfono si es WhatsApp
        if "whatsapp" in user_id.lower():
            phone_number = user_id.replace("whatsapp", "").replace("+", "")
            for filename in os.listdir(memory_dir):
                if phone_number in filename and filename not in [f["filename"] for f in found["memory_files"]]:
                    file_path = os.path.join(memory_dir, filename)
                    file_size = os.path.getsize(file_path)
                    found["memory_files"].append({
                        "filename": filename,
                        "size_bytes": file_size,
                        "path": file_path
                    })
                    found["total_files"] += 1
    
    # Escanear base de datos
    try:
        db = init_db()
        if db:
            state_db = ConversationStateDB(db)
            stats = state_db.get_user_stats(user_id)
            
            found["database_exists"] = stats.get("exists", False)
            found["database_stats"] = stats
            
    except Exception as e:
        found["database_error"] = str(e)
    
    return found

def list_all_users() -> list:
    """Listar todos los usuarios que tienen datos almacenados"""
    users = set()
    
    # Escanear archivos
    memory_dir = "user_memories_data"
    if os.path.exists(memory_dir):
        for filename in os.listdir(memory_dir):
            if filename.endswith('.json') and not filename.endswith('_backup.json'):
                user_id = filename.replace('.json', '')
                users.add(user_id)
    
    return sorted(list(users))

if __name__ == "__main__":
    print("🔍 UTILIDAD DE LIMPIEZA DE MEMORIA - AGENTE GLAMPING")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python clear_memory_utility.py scan <user_id>     # Ver qué datos existen")
        print("  python clear_memory_utility.py clear <user_id>    # Limpiar datos del usuario")
        print("  python clear_memory_utility.py list               # Listar todos los usuarios")
        print("")
        print("Ejemplos:")
        print("  python clear_memory_utility.py scan whatsapp573001234567")
        print("  python clear_memory_utility.py clear whatsapp573001234567")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        users = list_all_users()
        print(f"📋 USUARIOS CON DATOS ALMACENADOS ({len(users)}):")
        for user in users:
            print(f"  - {user}")
    
    elif command in ["scan", "clear"] and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        
        if command == "scan":
            data = scan_user_data(user_id)
            print(f"🔍 DATOS ENCONTRADOS PARA: {user_id}")
            print(f"  Archivos de memoria: {len(data['memory_files'])}")
            for file_info in data['memory_files']:
                print(f"    - {file_info['filename']} ({file_info['size_bytes']} bytes)")
            print(f"  Base de datos: {'✓' if data['database_exists'] else '❌'}")
            if data['database_exists']:
                stats = data['database_stats']
                print(f"    - Mensajes: {stats.get('total_messages', 0)}")
                print(f"    - Último flujo: {stats.get('current_flow', 'none')}")
                print(f"    - Última interacción: {stats.get('last_interaction', 'N/A')}")
        
        elif command == "clear":
            print("⚠️  ESTA OPERACIÓN ELIMINARÁ PERMANENTEMENTE TODOS LOS DATOS")
            response = input(f"¿Confirmar eliminación de datos para '{user_id}'? (escribe 'CONFIRMAR'): ")
            
            if response.strip().upper() == "CONFIRMAR":
                result = clear_user_memory(user_id, confirmation=True)
                print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                print("❌ Operación cancelada")
    
    else:
        print("❌ Comando inválido o faltan parámetros")
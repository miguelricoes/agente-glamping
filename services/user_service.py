# Servicio centralizado de gestión de usuarios
# Extrae funcionalidades de usuario de agente.py (líneas 309-423)

import secrets
import string
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from utils.logger import get_logger

logger = get_logger(__name__)

class UserService:
    """
    Servicio centralizado para gestión de usuarios
    Consolida operaciones CRUD y validaciones de usuarios
    """
    
    def __init__(self, db, Usuario):
        """
        Inicializar servicio de usuarios
        
        Args:
            db: Instancia de SQLAlchemy
            Usuario: Modelo de Usuario
        """
        self.db = db
        self.Usuario = Usuario
        logger.info("UserService inicializado", 
                   extra={"component": "user_service", "phase": "startup"})
    
    def generate_random_password(self, length: int = 8) -> str:
        """
        Genera contraseña aleatoria segura (extraído de agente.py líneas 310-317)
        
        Args:
            length: Longitud de la contraseña
            
        Returns:
            str: Contraseña generada
        """
        try:
            # Excluir caracteres confusos
            characters = string.ascii_letters + string.digits
            characters = characters.replace('0', '').replace('O', '').replace('l', '').replace('I', '')
            
            password = ''.join(secrets.choice(characters) for _ in range(length))
            
            logger.info(f"Contraseña aleatoria generada (longitud: {length})", 
                       extra={"component": "user_service", "action": "generate_password"})
            
            return password
            
        except Exception as e:
            logger.error(f"Error generando contraseña aleatoria: {e}", 
                        extra={"component": "user_service"})
            return "TempPass123"  # Fallback
    
    def generate_simple_password(self) -> str:
        """
        Genera contraseña simple de 8 caracteres (extraído de agente.py líneas 319-325)
        
        Returns:
            str: Contraseña simple
        """
        try:
            # Combinación de letras y números fáciles de recordar
            letters = 'abcdefghijkmnpqrstuvwxyz'  # Sin caracteres confusos
            numbers = '23456789'  # Sin 0 y 1
            
            password = (
                secrets.choice(letters.upper()) +
                secrets.choice(letters) +
                secrets.choice(numbers) +
                secrets.choice(letters) +
                secrets.choice(letters.upper()) +
                secrets.choice(numbers) +
                secrets.choice(letters) +
                secrets.choice(numbers)
            )
            
            logger.info("Contraseña simple generada", 
                       extra={"component": "user_service", "action": "generate_simple_password"})
            
            return password
            
        except Exception as e:
            logger.error(f"Error generando contraseña simple: {e}", 
                        extra={"component": "user_service"})
            return "Temp1234"  # Fallback
    
    def get_all_users(self, include_passwords: bool = False) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Obtiene todos los usuarios (extraído de agente.py líneas 328-354)
        
        Args:
            include_passwords: Si incluir información de contraseñas
            
        Returns:
            Tuple[bool, List[Dict], str]: (success, lista_usuarios, mensaje_error)
        """
        try:
            logger.info("Obteniendo todos los usuarios", 
                       extra={"component": "user_service", "action": "get_all_users"})
            
            if not self.db:
                return False, [], "Base de datos no disponible"
            
            usuarios = self.Usuario.query.all()
            usuarios_data = []
            
            for usuario in usuarios:
                user_dict = {
                    'id': usuario.id,
                    'nombre': usuario.nombre,
                    'email': usuario.email,
                    'rol': usuario.rol,
                    'fecha_creacion': usuario.fecha_creacion.isoformat() if usuario.fecha_creacion else None,
                    'activo': getattr(usuario, 'activo', True),
                    'ultimo_acceso': usuario.ultimo_acceso.isoformat() if getattr(usuario, 'ultimo_acceso', None) else None,
                    'password_changed': getattr(usuario, 'password_changed', False)
                }
                
                if include_passwords:
                    user_dict.update({
                        'tiene_password_hash': bool(getattr(usuario, 'password_hash', None)),
                        'tiene_temp_password': bool(getattr(usuario, 'temp_password', None))
                    })
                
                usuarios_data.append(user_dict)
            
            logger.info(f"Usuarios obtenidos exitosamente: {len(usuarios_data)}", 
                       extra={"component": "user_service", "users_count": len(usuarios_data)})
            
            return True, usuarios_data, ""
            
        except Exception as e:
            error_msg = f"Error obteniendo usuarios: {e}"
            logger.error(error_msg, extra={"component": "user_service"})
            return False, [], error_msg
    
    def create_user_function(self, nombre: str, email: str, password: Optional[str] = None, 
                           rol: str = 'limitado') -> Tuple[bool, Optional[int], str]:
        """
        Crea un nuevo usuario (extraído de agente.py líneas 356-388)
        
        Args:
            nombre: Nombre del usuario
            email: Email del usuario
            password: Contraseña (opcional, se genera automáticamente)
            rol: Rol del usuario
            
        Returns:
            Tuple[bool, int, str]: (success, user_id, mensaje)
        """
        try:
            logger.info(f"Creando usuario: {nombre} ({email})", 
                       extra={"component": "user_service", "action": "create_user"})
            
            if not self.db:
                return False, None, "Base de datos no disponible"
            
            # Validar que el email no exista
            existing_user = self.Usuario.query.filter_by(email=email).first()
            if existing_user:
                return False, None, f"Ya existe un usuario con el email {email}"
            
            # Generar contraseña si no se proporciona
            if not password:
                password = self.generate_simple_password()
            
            # Crear nuevo usuario
            nuevo_usuario = self.Usuario(
                nombre=nombre,
                email=email,
                password_hash=generate_password_hash(password),
                temp_password=password,  # Guardar temporalmente para mostrar al admin
                rol=rol,
                fecha_creacion=datetime.utcnow(),
                activo=True,
                password_changed=False
            )
            
            self.db.session.add(nuevo_usuario)
            self.db.session.commit()
            
            success_msg = f"Usuario {nombre} creado exitosamente con contraseña temporal: {password}"
            logger.info(f"Usuario creado exitosamente: ID {nuevo_usuario.id}", 
                       extra={"component": "user_service", "user_id": nuevo_usuario.id, "role": rol})
            
            return True, nuevo_usuario.id, success_msg
            
        except Exception as e:
            if self.db:
                self.db.session.rollback()
            error_msg = f"Error creando usuario: {e}"
            logger.error(error_msg, extra={"component": "user_service"})
            return False, None, error_msg
    
    def update_user_function(self, user_id: int, nombre: str, email: str, rol: str, 
                           activo: bool = True) -> Tuple[bool, str]:
        """
        Actualiza un usuario existente (extraído de agente.py líneas 390-407)
        
        Args:
            user_id: ID del usuario a actualizar
            nombre: Nuevo nombre
            email: Nuevo email
            rol: Nuevo rol
            activo: Estado activo
            
        Returns:
            Tuple[bool, str]: (success, mensaje)
        """
        try:
            logger.info(f"Actualizando usuario ID: {user_id}", 
                       extra={"component": "user_service", "action": "update_user", "user_id": user_id})
            
            if not self.db:
                return False, "Base de datos no disponible"
            
            usuario = self.Usuario.query.get(user_id)
            if not usuario:
                return False, f"Usuario con ID {user_id} no encontrado"
            
            # Verificar que el nuevo email no esté en uso por otro usuario
            if email != usuario.email:
                existing_user = self.Usuario.query.filter_by(email=email).first()
                if existing_user and existing_user.id != user_id:
                    return False, f"El email {email} ya está en uso por otro usuario"
            
            # Actualizar campos
            usuario.nombre = nombre
            usuario.email = email
            usuario.rol = rol
            if hasattr(usuario, 'activo'):
                usuario.activo = activo
            
            self.db.session.commit()
            
            success_msg = f"Usuario {nombre} actualizado exitosamente"
            logger.info(f"Usuario actualizado exitosamente: ID {user_id}", 
                       extra={"component": "user_service", "user_id": user_id})
            
            return True, success_msg
            
        except Exception as e:
            if self.db:
                self.db.session.rollback()
            error_msg = f"Error actualizando usuario: {e}"
            logger.error(error_msg, extra={"component": "user_service"})
            return False, error_msg
    
    def delete_user_function(self, user_id: int) -> Tuple[bool, str]:
        """
        Elimina un usuario (extraído de agente.py líneas 409-423)
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            Tuple[bool, str]: (success, mensaje)
        """
        try:
            logger.info(f"Eliminando usuario ID: {user_id}", 
                       extra={"component": "user_service", "action": "delete_user", "user_id": user_id})
            
            if not self.db:
                return False, "Base de datos no disponible"
            
            usuario = self.Usuario.query.get(user_id)
            if not usuario:
                return False, f"Usuario con ID {user_id} no encontrado"
            
            nombre = usuario.nombre
            
            self.db.session.delete(usuario)
            self.db.session.commit()
            
            success_msg = f"Usuario {nombre} eliminado exitosamente"
            logger.info(f"Usuario eliminado exitosamente: ID {user_id}", 
                       extra={"component": "user_service", "user_id": user_id})
            
            return True, success_msg
            
        except Exception as e:
            if self.db:
                self.db.session.rollback()
            error_msg = f"Error eliminando usuario: {e}"
            logger.error(error_msg, extra={"component": "user_service"})
            return False, error_msg
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Autentica un usuario
        
        Args:
            email: Email del usuario
            password: Contraseña
            
        Returns:
            Tuple[bool, Dict, str]: (success, user_data, mensaje)
        """
        try:
            logger.info(f"Autenticando usuario: {email}", 
                       extra={"component": "user_service", "action": "authenticate"})
            
            if not self.db:
                return False, None, "Base de datos no disponible"
            
            usuario = self.Usuario.query.filter_by(email=email).first()
            if not usuario:
                return False, None, "Credenciales inválidas"
            
            # Verificar contraseña
            password_valid = False
            if hasattr(usuario, 'check_password') and callable(usuario.check_password):
                password_valid = usuario.check_password(password)
            elif hasattr(usuario, 'password_hash') and usuario.password_hash:
                password_valid = check_password_hash(usuario.password_hash, password)
            
            if not password_valid:
                return False, None, "Credenciales inválidas"
            
            # Actualizar último acceso
            if hasattr(usuario, 'ultimo_acceso'):
                usuario.ultimo_acceso = datetime.utcnow()
                self.db.session.commit()
            
            user_data = {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol,
                'activo': getattr(usuario, 'activo', True),
                'password_changed': getattr(usuario, 'password_changed', False)
            }
            
            logger.info(f"Usuario autenticado exitosamente: {email}", 
                       extra={"component": "user_service", "user_id": usuario.id})
            
            return True, user_data, "Autenticación exitosa"
            
        except Exception as e:
            error_msg = f"Error en autenticación: {e}"
            logger.error(error_msg, extra={"component": "user_service"})
            return False, None, error_msg
    
    def regenerate_password(self, user_id: int) -> Tuple[bool, Optional[str], str]:
        """
        Regenera la contraseña de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Tuple[bool, str, str]: (success, nueva_password, mensaje)
        """
        try:
            logger.info(f"Regenerando contraseña para usuario ID: {user_id}", 
                       extra={"component": "user_service", "action": "regenerate_password", "user_id": user_id})
            
            if not self.db:
                return False, None, "Base de datos no disponible"
            
            usuario = self.Usuario.query.get(user_id)
            if not usuario:
                return False, None, f"Usuario con ID {user_id} no encontrado"
            
            # Generar nueva contraseña
            nueva_password = self.generate_simple_password()
            
            # Actualizar usuario
            if hasattr(usuario, 'set_password') and callable(usuario.set_password):
                usuario.set_password(nueva_password)
            else:
                usuario.password_hash = generate_password_hash(nueva_password)
            
            if hasattr(usuario, 'temp_password'):
                usuario.temp_password = nueva_password
            
            if hasattr(usuario, 'password_changed'):
                usuario.password_changed = False
            
            self.db.session.commit()
            
            success_msg = f"Contraseña regenerada para {usuario.nombre}"
            logger.info(f"Contraseña regenerada exitosamente para usuario ID: {user_id}", 
                       extra={"component": "user_service", "user_id": user_id})
            
            return True, nueva_password, success_msg
            
        except Exception as e:
            if self.db:
                self.db.session.rollback()
            error_msg = f"Error regenerando contraseña: {e}"
            logger.error(error_msg, extra={"component": "user_service"})
            return False, None, error_msg
    
    def get_user_by_id(self, user_id: int) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Obtiene un usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Tuple[bool, Dict, str]: (success, user_data, mensaje)
        """
        try:
            if not self.db:
                return False, None, "Base de datos no disponible"
            
            usuario = self.Usuario.query.get(user_id)
            if not usuario:
                return False, None, f"Usuario con ID {user_id} no encontrado"
            
            user_data = {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol,
                'fecha_creacion': usuario.fecha_creacion.isoformat() if usuario.fecha_creacion else None,
                'activo': getattr(usuario, 'activo', True),
                'ultimo_acceso': usuario.ultimo_acceso.isoformat() if getattr(usuario, 'ultimo_acceso', None) else None,
                'password_changed': getattr(usuario, 'password_changed', False)
            }
            
            logger.info(f"Usuario obtenido por ID: {user_id}", 
                       extra={"component": "user_service", "user_id": user_id})
            
            return True, user_data, ""
            
        except Exception as e:
            error_msg = f"Error obteniendo usuario por ID: {e}"
            logger.error(error_msg, extra={"component": "user_service"})
            return False, None, error_msg
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Obtiene estado de salud del servicio de usuarios
        
        Returns:
            Dict[str, Any]: Estado de salud
        """
        try:
            health_status = {
                'service_name': 'UserService',
                'status': 'healthy',
                'database_available': self.db is not None,
                'model_available': self.Usuario is not None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if self.db:
                try:
                    # Test básico de conexión
                    user_count = self.Usuario.query.count()
                    health_status.update({
                        'database_connection': 'ok',
                        'user_count': user_count
                    })
                except Exception as e:
                    health_status.update({
                        'status': 'degraded',
                        'database_connection': 'error',
                        'database_error': str(e)
                    })
            else:
                health_status.update({
                    'status': 'degraded',
                    'database_connection': 'unavailable'
                })
            
            return health_status
            
        except Exception as e:
            return {
                'service_name': 'UserService',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


def get_user_service(db, Usuario) -> UserService:
    """
    Factory function para crear instancia de UserService
    
    Args:
        db: Instancia de SQLAlchemy
        Usuario: Modelo de Usuario
        
    Returns:
        UserService: Instancia del servicio
    """
    return UserService(db, Usuario)
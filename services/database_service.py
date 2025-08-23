# Servicio centralizado de base de datos - Extrae operaciones CRUD de agente.py
# Centraliza todas las operaciones de base de datos para mejor organización y mantenimiento

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from utils.logger import get_logger, log_database_operation, log_error

# Inicializar logger para este módulo
logger = get_logger(__name__)

class DatabaseService:
    """
    Servicio centralizado para todas las operaciones de base de datos
    Extrae y organiza las operaciones CRUD de reservas y usuarios
    """
    
    def __init__(self, db, Reserva=None, Usuario=None, persistent_state_service=None):
        """
        Inicializar servicio de base de datos
        
        Args:
            db: Instancia de SQLAlchemy
            Reserva: Modelo de Reserva
            Usuario: Modelo de Usuario
            persistent_state_service: Servicio de estado persistente para invalidar cache
        """
        self.db = db
        self.Reserva = Reserva
        self.Usuario = Usuario
        self.persistent_state_service = persistent_state_service
        
        logger.info("Servicio de base de datos inicializado",
                   extra={"phase": "startup", "component": "database_service", 
                          "cache_integration": persistent_state_service is not None})
    
    def _check_database_available(self) -> bool:
        """Verificar que la base de datos esté disponible"""
        return self.db is not None and self.Reserva is not None and self.Usuario is not None
    
    def _invalidate_user_cache(self, user_id: str = None) -> None:
        """Invalidar cache de estado de usuario específico o todos"""
        if self.persistent_state_service and hasattr(self.persistent_state_service, '_clear_cache'):
            try:
                if user_id:
                    self.persistent_state_service._clear_cache(user_id)
                    logger.debug(f"Cache invalidado para usuario: {user_id}",
                               extra={"component": "database_service", "action": "cache_invalidation"})
                else:
                    # Invalidar todo el cache
                    if hasattr(self.persistent_state_service, '_state_cache'):
                        self.persistent_state_service._state_cache.clear()
                        self.persistent_state_service._memory_cache.clear()
                        self.persistent_state_service._cache_timestamps.clear()
                        logger.debug("Cache global invalidado",
                                   extra={"component": "database_service", "action": "global_cache_invalidation"})
            except Exception as e:
                logger.warning(f"Error invalidando cache: {e}",
                             extra={"component": "database_service", "user_id": user_id})
    
    @contextmanager
    def atomic_transaction(self):
        """Context manager para transacciones atómicas con invalidación de cache"""
        try:
            yield
            self.db.session.commit()
            logger.debug("Transacción atómica confirmada",
                       extra={"component": "database_service"})
        except SQLAlchemyError as e:
            self.db.session.rollback()
            logger.error(f"Error en transacción atómica, rollback ejecutado: {e}",
                       extra={"component": "database_service"})
            raise
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error inesperado en transacción, rollback ejecutado: {e}",
                       extra={"component": "database_service"})
            raise
    
    # ===== OPERACIONES DE RESERVAS =====
    
    def get_all_reservas(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Obtener todas las reservas con formateo para frontend
        
        Returns:
            Tupla (success, reservas_data, error_message)
        """
        try:
            if not self._check_database_available():
                return False, [], "Base de datos no disponible"
            
            # Obtener todas las reservas ordenadas por fecha de creación
            reservas = self.Reserva.query.order_by(self.Reserva.fecha_creacion.desc()).all()
            
            # Formatear datos para el frontend
            reservas_data = []
            for reserva in reservas:
                # Procesar servicios - convertir string a array de objetos
                servicios_array = []
                if reserva.servicio_elegido and reserva.servicio_elegido != 'Ninguno':
                    servicios_string = reserva.servicio_elegido
                    servicios_lista = [s.strip() for s in servicios_string.split(',') if s.strip()]

                    for servicio in servicios_lista:
                        servicios_array.append({
                            'nombre': servicio,
                            'precio': 0,  
                            'descripcion': ''
                        })

                reserva_item = {
                    'id': reserva.id,
                    'numeroWhatsapp': reserva.numero_whatsapp,
                    'emailContacto': reserva.email_contacto,
                    'cantidadHuespedes': reserva.cantidad_huespedes,
                    'domo': reserva.domo,
                    'fechaEntrada': reserva.fecha_entrada.isoformat() if reserva.fecha_entrada else None,
                    'fechaSalida': reserva.fecha_salida.isoformat() if reserva.fecha_salida else None,
                    'metodoPago': reserva.metodo_pago,
                    'nombresHuespedes': reserva.nombres_huespedes,
                    'servicios': servicios_array,
                    'adicciones': reserva.adicciones,
                    'comentariosEspeciales': reserva.comentarios_especiales,
                    'numeroContacto': reserva.numero_contacto,
                    'montoTotal': float(reserva.monto_total) if reserva.monto_total else 0.0,
                    'fechaCreacion': reserva.fecha_creacion.isoformat() if reserva.fecha_creacion else None
                }
                reservas_data.append(reserva_item)
            
            log_database_operation(logger, "SELECT", "reservas", True, 
                                 f"Obtenidas {len(reservas_data)} reservas")
            
            return True, reservas_data, ""
            
        except Exception as e:
            error_msg = f"Error obteniendo reservas: {str(e)}"
            log_database_operation(logger, "SELECT", "reservas", False, error_msg)
            return False, [], error_msg
    
    def get_reservas_stats(self) -> Tuple[bool, Dict[str, Any], str]:
        """
        Obtener estadísticas de reservas
        
        Returns:
            Tupla (success, stats_data, error_message)
        """
        try:
            if not self._check_database_available():
                return False, {}, "Base de datos no disponible"
            
            # Total de reservas
            total_reservas = self.Reserva.query.count()
            
            # Reservas del mes actual
            from datetime import datetime
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            reservas_mes = self.Reserva.query.filter(
                self.db.extract('month', self.Reserva.fecha_creacion) == current_month,
                self.db.extract('year', self.Reserva.fecha_creacion) == current_year
            ).count()
            
            # Reservas por domo
            reservas_por_domo = self.db.session.query(
                self.Reserva.domo, 
                self.db.func.count(self.Reserva.id).label('cantidad')
            ).filter(self.Reserva.domo.isnot(None)).group_by(self.Reserva.domo).all()
            
            stats_data = {
                "total_reservas": total_reservas or 0,
                "reservas_mes_actual": reservas_mes or 0,
                "reservas_por_domo": [
                    {"domo": domo, "cantidad": cantidad} 
                    for domo, cantidad in reservas_por_domo
                ]
            }
            
            log_database_operation(logger, "STATS", "reservas", True, 
                                 f"Estadísticas calculadas: {total_reservas} total")
            
            return True, stats_data, ""
            
        except Exception as e:
            error_msg = f"Error obteniendo estadísticas: {str(e)}"
            log_database_operation(logger, "STATS", "reservas", False, error_msg)
            return False, {}, error_msg
    
    def create_reserva(self, reserva_data: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
        """
        Crear nueva reserva
        
        Args:
            reserva_data: Diccionario con datos de la reserva
            
        Returns:
            Tupla (success, reserva_id, error_message)
        """
        try:
            if not self._check_database_available():
                return False, None, "Base de datos no disponible"
            
            # Validar campos importantes
            validation_result = self._validate_reserva_fields(reserva_data)
            if not validation_result['valido']:
                return False, None, f"Campos inválidos: {validation_result['errores']}"
            
            # Crear nueva reserva
            nueva_reserva = self.Reserva(
                numero_whatsapp=reserva_data.get('numero_whatsapp'),
                nombres_huespedes=reserva_data.get('nombres_huespedes'),
                cantidad_huespedes=reserva_data.get('cantidad_huespedes'),
                domo=reserva_data.get('domo'),
                fecha_entrada=datetime.strptime(reserva_data.get('fecha_entrada'), '%Y-%m-%d').date(),
                fecha_salida=datetime.strptime(reserva_data.get('fecha_salida'), '%Y-%m-%d').date(),
                servicio_elegido=reserva_data.get('servicio_elegido'),
                adicciones=reserva_data.get('adicciones'),
                numero_contacto=reserva_data.get('numero_contacto'),
                email_contacto=reserva_data.get('email_contacto'),
                metodo_pago=reserva_data.get('metodo_pago', 'Pendiente'),
                monto_total=Decimal(str(reserva_data.get('monto_total', 0))),
                comentarios_especiales=reserva_data.get('comentarios_especiales')
            )
            
            with self.atomic_transaction():
                self.db.session.add(nueva_reserva)
                
                # Invalidar cache del usuario asociado a la reserva
                user_id = reserva_data.get('numero_whatsapp')
                if user_id:
                    self._invalidate_user_cache(user_id)
            
            log_database_operation(logger, "INSERT", "reservas", True, 
                                 f"Reserva creada con ID: {nueva_reserva.id}")
            
            return True, nueva_reserva.id, ""
            
        except Exception as e:
            self.db.session.rollback()
            error_msg = f"Error creando reserva: {str(e)}"
            log_database_operation(logger, "INSERT", "reservas", False, error_msg)
            return False, None, error_msg
    
    def update_reserva(self, reserva_id: int, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Actualizar reserva existente
        
        Args:
            reserva_id: ID de la reserva
            update_data: Datos a actualizar
            
        Returns:
            Tupla (success, error_message)
        """
        try:
            if not self._check_database_available():
                return False, "Base de datos no disponible"
            
            reserva = self.Reserva.query.get(reserva_id)
            if not reserva:
                return False, "Reserva no encontrada"
            
            # Actualizar campos
            updatable_fields = [
                'numero_whatsapp', 'nombres_huespedes', 'cantidad_huespedes', 'domo',
                'fecha_entrada', 'fecha_salida', 'servicio_elegido', 'adicciones',
                'numero_contacto', 'email_contacto', 'metodo_pago', 'monto_total',
                'comentarios_especiales'
            ]
            
            for field in updatable_fields:
                if field in update_data:
                    if field in ['fecha_entrada', 'fecha_salida']:
                        setattr(reserva, field, datetime.strptime(update_data[field], '%Y-%m-%d').date())
                    elif field == 'monto_total':
                        setattr(reserva, field, Decimal(str(update_data[field])))
                    else:
                        setattr(reserva, field, update_data[field])
            
            with self.atomic_transaction():
                # Invalidar cache del usuario asociado (tanto el original como el actualizado)
                if reserva.numero_whatsapp:
                    self._invalidate_user_cache(reserva.numero_whatsapp)
                
                # Si se cambió el número de WhatsApp, invalidar cache del nuevo usuario también
                new_whatsapp = update_data.get('numero_whatsapp')
                if new_whatsapp and new_whatsapp != reserva.numero_whatsapp:
                    self._invalidate_user_cache(new_whatsapp)
            
            log_database_operation(logger, "UPDATE", "reservas", True, 
                                 f"Reserva {reserva_id} actualizada")
            
            return True, ""
            
        except Exception as e:
            self.db.session.rollback()
            error_msg = f"Error actualizando reserva: {str(e)}"
            log_database_operation(logger, "UPDATE", "reservas", False, error_msg)
            return False, error_msg
    
    def delete_reserva(self, reserva_id: int) -> Tuple[bool, str]:
        """
        Eliminar reserva
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Tupla (success, error_message)
        """
        try:
            if not self._check_database_available():
                return False, "Base de datos no disponible"
            
            reserva = self.Reserva.query.get(reserva_id)
            if not reserva:
                return False, "Reserva no encontrada"
            
            with self.atomic_transaction():
                # Invalidar cache del usuario asociado antes de eliminar
                if reserva.numero_whatsapp:
                    self._invalidate_user_cache(reserva.numero_whatsapp)
                    
                self.db.session.delete(reserva)
            
            log_database_operation(logger, "DELETE", "reservas", True, 
                                 f"Reserva {reserva_id} eliminada")
            
            return True, ""
            
        except Exception as e:
            self.db.session.rollback()
            error_msg = f"Error eliminando reserva: {str(e)}"
            log_database_operation(logger, "DELETE", "reservas", False, error_msg)
            return False, error_msg
    
    def _validate_reserva_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar campos importantes de reserva
        
        Args:
            data: Datos de la reserva
            
        Returns:
            Diccionario con resultado de validación
        """
        required_fields = [
            'numero_whatsapp', 'email_contacto', 'cantidad_huespedes', 
            'domo', 'fecha_entrada', 'fecha_salida', 'metodo_pago'
        ]
        
        errores = []
        
        for field in required_fields:
            if not data.get(field):
                errores.append(f"Campo requerido: {field}")
        
        # Validaciones específicas
        if data.get('cantidad_huespedes'):
            try:
                huespedes = int(data['cantidad_huespedes'])
                if huespedes <= 0 or huespedes > 20:
                    errores.append("Cantidad de huéspedes debe ser entre 1 y 20")
            except (ValueError, TypeError):
                errores.append("Cantidad de huéspedes debe ser un número")
        
        if data.get('email_contacto'):
            email = data['email_contacto']
            if '@' not in email or '.' not in email:
                errores.append("Email inválido")
        
        return {
            'valido': len(errores) == 0,
            'errores': errores
        }
    
    # ===== OPERACIONES DE USUARIOS =====
    
    def get_all_users(self, include_passwords: bool = False) -> List[Dict[str, Any]]:
        """
        Obtener todos los usuarios
        
        Args:
            include_passwords: Si incluir contraseñas temporales
            
        Returns:
            Lista de usuarios
        """
        try:
            if not self._check_database_available():
                return []
            
            usuarios = self.Usuario.query.order_by(self.Usuario.fecha_creacion.desc()).all()
            result = []
            
            for u in usuarios:
                user_data = {
                    'id': u.id,
                    'nombre': u.nombre,
                    'email': u.email,
                    'rol': u.rol,
                    'fecha_creacion': u.fecha_creacion.isoformat() if u.fecha_creacion else None,
                    'ultimo_acceso': u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
                    'activo': u.activo,
                    'password_changed': u.password_changed or False
                }
                
                # Solo incluir contraseña si se solicita (solo para admin)
                if include_passwords and hasattr(u, 'temp_password') and u.temp_password:
                    user_data['temp_password'] = u.temp_password
                
                result.append(user_data)
            
            log_database_operation(logger, "SELECT", "usuarios", True, 
                                 f"Obtenidos {len(result)} usuarios")
            
            return result
            
        except Exception as e:
            log_database_operation(logger, "SELECT", "usuarios", False, str(e))
            return []
    
    def create_user(self, nombre: str, email: str, password: str = None, rol: str = 'limitado') -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Crear nuevo usuario con contraseña generada automáticamente
        
        Args:
            nombre: Nombre del usuario
            email: Email del usuario
            password: Contraseña (opcional, se genera automáticamente)
            rol: Rol del usuario
            
        Returns:
            Tupla (success, user_data, error_message)
        """
        try:
            if not self._check_database_available():
                return False, None, "Base de datos no disponible"
            
            # Verificar si el email ya existe
            existing_user = self.Usuario.query.filter_by(email=email).first()
            if existing_user:
                return False, None, "Email ya existe"
            
            # Generar contraseña si no se proporciona
            if not password:
                password = self._generate_simple_password()
            
            # Crear usuario
            from werkzeug.security import generate_password_hash
            nuevo_usuario = self.Usuario(
                nombre=nombre,
                email=email,
                password_hash=generate_password_hash(password),
                temp_password=password,
                rol=rol,
                activo=True,
                password_changed=False,
                fecha_creacion=datetime.utcnow()
            )
            
            with self.atomic_transaction():
                self.db.session.add(nuevo_usuario)
            
            # Invalidar cache global después de crear usuario
            self._invalidate_user_cache()
            
            user_data = {
                'id': nuevo_usuario.id,
                'nombre': nuevo_usuario.nombre,
                'email': nuevo_usuario.email,
                'temp_password': password,
                'rol': nuevo_usuario.rol
            }
            
            log_database_operation(logger, "INSERT", "usuarios", True, 
                                 f"Usuario creado: {email}")
            
            return True, user_data, ""
            
        except Exception as e:
            self.db.session.rollback()
            error_msg = f"Error creando usuario: {str(e)}"
            log_database_operation(logger, "INSERT", "usuarios", False, error_msg)
            return False, None, error_msg
    
    def update_user(self, user_id: int, nombre: str, email: str, rol: str, activo: bool = True) -> Tuple[bool, str]:
        """
        Actualizar usuario existente
        
        Args:
            user_id: ID del usuario
            nombre: Nuevo nombre
            email: Nuevo email
            rol: Nuevo rol
            activo: Estado activo
            
        Returns:
            Tupla (success, error_message)
        """
        try:
            if not self._check_database_available():
                return False, "Base de datos no disponible"
            
            usuario = self.Usuario.query.get(user_id)
            if not usuario:
                return False, "Usuario no encontrado"
            
            # Verificar email único (excepto el mismo usuario)
            existing_user = self.Usuario.query.filter(
                self.Usuario.email == email,
                self.Usuario.id != user_id
            ).first()
            
            if existing_user:
                return False, "Email ya existe en otro usuario"
            
            with self.atomic_transaction():
                # Actualizar campos
                usuario.nombre = nombre
                usuario.email = email
                usuario.rol = rol
                usuario.activo = activo
            
            # Invalidar cache global después de actualizar usuario
            self._invalidate_user_cache()
            
            log_database_operation(logger, "UPDATE", "usuarios", True, 
                                 f"Usuario {user_id} actualizado")
            
            return True, ""
            
        except Exception as e:
            self.db.session.rollback()
            error_msg = f"Error actualizando usuario: {str(e)}"
            log_database_operation(logger, "UPDATE", "usuarios", False, error_msg)
            return False, error_msg
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """
        Eliminar usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Tupla (success, error_message)
        """
        try:
            if not self._check_database_available():
                return False, "Base de datos no disponible"
            
            usuario = self.Usuario.query.get(user_id)
            if not usuario:
                return False, "Usuario no encontrado"
            
            with self.atomic_transaction():
                self.db.session.delete(usuario)
            
            # Invalidar cache global después de eliminar usuario
            self._invalidate_user_cache()
            
            log_database_operation(logger, "DELETE", "usuarios", True, 
                                 f"Usuario {user_id} eliminado")
            
            return True, ""
            
        except Exception as e:
            self.db.session.rollback()
            error_msg = f"Error eliminando usuario: {str(e)}"
            log_database_operation(logger, "DELETE", "usuarios", False, error_msg)
            return False, error_msg
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Autenticar usuario
        
        Args:
            email: Email del usuario
            password: Contraseña
            
        Returns:
            Datos del usuario si la autenticación es exitosa, None en caso contrario
        """
        try:
            if not self._check_database_available():
                return None
            
            from werkzeug.security import check_password_hash
            
            usuario = self.Usuario.query.filter_by(email=email, activo=True).first()
            
            if not usuario:
                return None
            
            # Verificar contraseña
            password_valid = False
            
            # Verificar contra password_hash (principal)
            if usuario.password_hash and check_password_hash(usuario.password_hash, password):
                password_valid = True
            # Verificar contra temp_password (respaldo)
            elif hasattr(usuario, 'temp_password') and usuario.temp_password == password:
                password_valid = True
            
            if not password_valid:
                return None
            
            # Actualizar último acceso de forma atómica
            with self.atomic_transaction():
                usuario.ultimo_acceso = datetime.utcnow()
            
            user_data = {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol,
                'password_changed': usuario.password_changed or False
            }
            
            log_database_operation(logger, "AUTH", "usuarios", True, 
                                 f"Usuario autenticado: {email}")
            
            return user_data
            
        except Exception as e:
            log_database_operation(logger, "AUTH", "usuarios", False, str(e))
            return None
    
    def regenerate_user_password(self, user_id: int) -> Tuple[bool, Optional[str], str]:
        """
        Regenerar contraseña de usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Tupla (success, new_password, error_message)
        """
        try:
            if not self._check_database_available():
                return False, None, "Base de datos no disponible"
            
            user = self.Usuario.query.get(user_id)
            if not user:
                return False, None, "Usuario no encontrado"
            
            # Generar nueva contraseña
            new_password = self._generate_simple_password()
            
            with self.atomic_transaction():
                # Actualizar contraseña
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash(new_password)
                user.temp_password = new_password
                user.password_changed = False
            
            # Invalidar cache global después de regenerar contraseña
            self._invalidate_user_cache()
            
            log_database_operation(logger, "UPDATE", "usuarios", True, 
                                 f"Contraseña regenerada para usuario {user_id}")
            
            return True, new_password, ""
            
        except Exception as e:
            self.db.session.rollback()
            error_msg = f"Error regenerando contraseña: {str(e)}"
            log_database_operation(logger, "UPDATE", "usuarios", False, error_msg)
            return False, None, error_msg
    
    def _generate_simple_password(self) -> str:
        """Generar contraseña simple"""
        import random
        import string
        
        # Generar contraseña de 8 caracteres
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(8))
    
    # ===== OPERACIONES ADICIONALES =====
    
    def get_database_health(self) -> Dict[str, Any]:
        """
        Obtener estado de salud de la base de datos
        
        Returns:
            Diccionario con información de salud
        """
        try:
            if not self._check_database_available():
                return {
                    "status": "unavailable",
                    "database_connected": False,
                    "tables_available": False
                }
            
            # Probar consultas básicas
            total_reservas = self.Reserva.query.count()
            total_usuarios = self.Usuario.query.count()
            
            return {
                "status": "healthy",
                "database_connected": True,
                "tables_available": True,
                "total_reservas": total_reservas,
                "total_usuarios": total_usuarios,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            log_error(logger, e, {"component": "database_health"})
            return {
                "status": "error",
                "database_connected": False,
                "tables_available": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
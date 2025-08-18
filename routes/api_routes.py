# Rutas API centralizadas - Agrupa todos los endpoints REST de agente.py
# Consolida endpoints de reservas, usuarios, disponibilidades, auth y health

from flask import request, jsonify
from datetime import datetime
from utils.logger import get_logger, log_request, log_response, log_error
from werkzeug.security import check_password_hash, generate_password_hash
import string
import random

# Inicializar logger para este módulo
logger = get_logger(__name__)

def register_api_routes(app, db=None, Reserva=None, Usuario=None, database_available=False, database_url=None, database_service=None, availability_service=None):
    """
    Registrar todas las rutas API centralizadas
    
    Args:
        app: Instancia de Flask
        db: Instancia de SQLAlchemy
        Reserva: Modelo de Reserva
        Usuario: Modelo de Usuario
        database_available: Estado de disponibilidad de la base de datos
        database_url: URL de la base de datos
        database_service: Instancia de DatabaseService (opcional, para nuevas rutas)
    """
    
    logger.info("Registrando rutas API centralizadas",
               extra={"phase": "startup", "component": "api_routes"})
    
    # ===== ENDPOINTS DE RESERVAS =====
    
    @app.route('/api/reservas', methods=['GET'])
    def get_reservas():
        """Obtener todas las reservas - Endpoint original"""
        
        log_request(logger, "/api/reservas")
        
        try:
            # Verificar estado de la base de datos
            if not database_available or not db:
                return jsonify({
                    'success': False,
                    'error': 'Base de datos no disponible',
                    'reservas': []
                }), 503
            
            # Obtener todas las reservas ordenadas por fecha de creación
            reservas = Reserva.query.order_by(Reserva.fecha_creacion.desc()).all()
            
            # Formatear datos para el frontend con mapeo correcto
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

                # Calcular monto total
                monto_total = 0
                if hasattr(reserva, 'monto_total') and reserva.monto_total:
                    monto_total = float(reserva.monto_total)
                else:
                    # Precio básico por domo (fallback)
                    precios_base = {
                        'antares': 650000,
                        'polaris': 550000,
                        'sirius': 450000,
                        'centaury': 450000
                    }
                    domo_lower = (reserva.domo or '').lower()
                    monto_total = precios_base.get(domo_lower, 450000)

                # Crear objeto de reserva con mapeo correcto para frontend
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
                    'montoTotal': monto_total,
                    'fechaCreacion': reserva.fecha_creacion.isoformat() if reserva.fecha_creacion else None
                }
                reservas_data.append(reserva_item)
            
            response = {
                'success': True,
                'count': len(reservas_data),
                'reservas': reservas_data
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/reservas"})
            return jsonify({
                'success': False,
                'error': 'Error interno del servidor',
                'reservas': []
            }), 500

    @app.route('/api/reservas/stats', methods=['GET'])
    def get_reservas_stats():
        """Obtener estadísticas de reservas"""
        
        log_request(logger, "/api/reservas/stats")
        
        try:
            if not database_available or not db:
                return jsonify({
                    'error': 'Base de datos no disponible'
                }), 503

            # Total de reservas
            total_reservas = Reserva.query.count()
            
            # Reservas del mes actual
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            reservas_mes = Reserva.query.filter(
                db.extract('month', Reserva.fecha_creacion) == current_month,
                db.extract('year', Reserva.fecha_creacion) == current_year
            ).count()
            
            # Reservas por domo
            reservas_por_domo = db.session.query(
                Reserva.domo, 
                db.func.count(Reserva.id).label('cantidad')
            ).filter(Reserva.domo.isnot(None)).group_by(Reserva.domo).all()
            
            stats_data = {
                "total_reservas": total_reservas or 0,
                "reservas_mes_actual": reservas_mes or 0,
                "reservas_por_domo": [
                    {"domo": domo, "cantidad": cantidad} 
                    for domo, cantidad in reservas_por_domo
                ]
            }
            
            return jsonify(stats_data), 200
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/reservas/stats"})
            return jsonify({"error": str(e)}), 500

    @app.route('/api/reservas', methods=['POST'])
    def create_reserva():
        """Crear nueva reserva con validación de campos importantes"""
        
        log_request(logger, "/api/reservas", method="POST")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Datos requeridos'}), 400

            # Validar campos requeridos
            required_fields = ['numero_whatsapp', 'email_contacto', 'cantidad_huespedes', 
                             'domo', 'fecha_entrada', 'fecha_salida', 'metodo_pago']
            
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'Campo requerido: {field}'}), 400

            # Crear nueva reserva
            nueva_reserva = Reserva(
                numero_whatsapp=data['numero_whatsapp'],
                nombres_huespedes=data.get('nombres_huespedes'),
                cantidad_huespedes=data['cantidad_huespedes'],
                domo=data['domo'],
                fecha_entrada=datetime.strptime(data['fecha_entrada'], '%Y-%m-%d').date(),
                fecha_salida=datetime.strptime(data['fecha_salida'], '%Y-%m-%d').date(),
                servicio_elegido=data.get('servicio_elegido'),
                adicciones=data.get('adicciones'),
                numero_contacto=data.get('numero_contacto'),
                email_contacto=data['email_contacto'],
                metodo_pago=data.get('metodo_pago', 'Pendiente'),
                monto_total=data.get('monto_total', 0),
                comentarios_especiales=data.get('comentarios_especiales')
            )
            
            db.session.add(nueva_reserva)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Reserva creada exitosamente',
                'reserva_id': nueva_reserva.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            log_error(logger, e, {"endpoint": "/api/reservas", "method": "POST"})
            return jsonify({'error': str(e)}), 500

    @app.route('/api/reservas/<reserva_id>', methods=['PUT'])
    def update_reserva(reserva_id):
        """Actualizar reserva existente"""
        
        log_request(logger, f"/api/reservas/{reserva_id}", method="PUT")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            reserva = Reserva.query.get(reserva_id)
            if not reserva:
                return jsonify({'error': 'Reserva no encontrada'}), 404

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Datos requeridos'}), 400

            # Actualizar campos
            updatable_fields = [
                'numero_whatsapp', 'nombres_huespedes', 'cantidad_huespedes', 'domo',
                'fecha_entrada', 'fecha_salida', 'servicio_elegido', 'adicciones',
                'numero_contacto', 'email_contacto', 'metodo_pago', 'monto_total',
                'comentarios_especiales'
            ]
            
            for field in updatable_fields:
                if field in data:
                    if field in ['fecha_entrada', 'fecha_salida']:
                        setattr(reserva, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                    else:
                        setattr(reserva, field, data[field])

            db.session.commit()
            return jsonify({'message': 'Reserva actualizada exitosamente'}), 200
            
        except Exception as e:
            db.session.rollback()
            log_error(logger, e, {"endpoint": f"/api/reservas/{reserva_id}", "method": "PUT"})
            return jsonify({'error': str(e)}), 500

    @app.route('/api/reservas/<reserva_id>', methods=['DELETE'])
    def delete_reserva(reserva_id):
        """Eliminar reserva"""
        
        log_request(logger, f"/api/reservas/{reserva_id}", method="DELETE")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            reserva = Reserva.query.get(reserva_id)
            if not reserva:
                return jsonify({'error': 'Reserva no encontrada'}), 404

            db.session.delete(reserva)
            db.session.commit()
            
            return jsonify({'message': 'Reserva eliminada exitosamente'}), 200
            
        except Exception as e:
            db.session.rollback()
            log_error(logger, e, {"endpoint": f"/api/reservas/{reserva_id}", "method": "DELETE"})
            return jsonify({'error': str(e)}), 500

    # ===== ENDPOINTS DE USUARIOS =====
    
    @app.route('/api/usuarios', methods=['GET'])
    def get_usuarios():
        """Obtener lista de usuarios"""
        
        log_request(logger, "/api/usuarios")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            usuarios = Usuario.query.order_by(Usuario.fecha_creacion.desc()).all()
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
                result.append(user_data)
            
            return jsonify(result), 200
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/usuarios"})
            return jsonify({'error': str(e)}), 500

    @app.route('/api/usuarios', methods=['POST'])
    def create_user_endpoint():
        """Crear nuevo usuario con contraseña generada"""
        
        log_request(logger, "/api/usuarios", method="POST")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            data = request.json
            nombre = data.get('nombre')
            email = data.get('email')
            rol = data.get('rol', 'limitado')
            
            if not nombre or not email:
                return jsonify({'error': 'Nombre y email son requeridos'}), 400

            # Verificar si el email ya existe
            existing_user = Usuario.query.filter_by(email=email).first()
            if existing_user:
                return jsonify({'error': 'Email ya existe'}), 400

            # Generar contraseña simple
            temp_password = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
            
            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email,
                password_hash=generate_password_hash(temp_password),
                temp_password=temp_password,
                rol=rol,
                activo=True,
                password_changed=False,
                fecha_creacion=datetime.utcnow()
            )
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'id': nuevo_usuario.id,
                'nombre': nuevo_usuario.nombre,
                'temp_password': temp_password
            }), 201
            
        except Exception as e:
            db.session.rollback()
            log_error(logger, e, {"endpoint": "/api/usuarios", "method": "POST"})
            return jsonify({'error': str(e)}), 400

    @app.route('/api/usuarios/<int:user_id>', methods=['PUT'])
    def update_user_endpoint(user_id):
        """Actualizar usuario"""
        
        log_request(logger, f"/api/usuarios/{user_id}", method="PUT")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            data = request.json
            nombre = data.get('nombre')
            email = data.get('email')
            rol = data.get('rol')
            activo = data.get('activo', True)
            
            if not nombre or not email or not rol:
                return jsonify({'error': 'Nombre, email y rol son requeridos'}), 400

            usuario = Usuario.query.get(user_id)
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 404

            # Verificar email único
            existing_user = Usuario.query.filter(
                Usuario.email == email,
                Usuario.id != user_id
            ).first()
            
            if existing_user:
                return jsonify({'error': 'Email ya existe en otro usuario'}), 400

            # Actualizar
            usuario.nombre = nombre
            usuario.email = email
            usuario.rol = rol
            usuario.activo = activo
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Usuario actualizado'}), 200
            
        except Exception as e:
            db.session.rollback()
            log_error(logger, e, {"endpoint": f"/api/usuarios/{user_id}", "method": "PUT"})
            return jsonify({'error': str(e)}), 400

    @app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
    def delete_user_endpoint(user_id):
        """Eliminar usuario"""
        
        log_request(logger, f"/api/usuarios/{user_id}", method="DELETE")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            usuario = Usuario.query.get(user_id)
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 404

            db.session.delete(usuario)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Usuario eliminado'}), 200
            
        except Exception as e:
            db.session.rollback()
            log_error(logger, e, {"endpoint": f"/api/usuarios/{user_id}", "method": "DELETE"})
            return jsonify({'error': str(e)}), 400

    @app.route('/api/usuarios/<int:user_id>/regenerate-password', methods=['POST'])
    def regenerate_password(user_id):
        """Regenerar contraseña para un usuario"""
        
        log_request(logger, f"/api/usuarios/{user_id}/regenerate-password")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            user = Usuario.query.get(user_id)
            if not user:
                return jsonify({'error': 'Usuario no encontrado'}), 404

            # Generar nueva contraseña
            new_password = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
            
            user.password_hash = generate_password_hash(new_password)
            user.temp_password = new_password
            user.password_changed = False
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'temp_password': new_password,
                'message': 'Contraseña regenerada exitosamente'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            log_error(logger, e, {"endpoint": f"/api/usuarios/{user_id}/regenerate-password"})
            return jsonify({'error': str(e)}), 400

    # ===== ENDPOINTS DE AUTENTICACIÓN =====
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Login de usuario con validación de PostgreSQL"""
        
        log_request(logger, "/api/auth/login")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            data = request.json
            if not data:
                return jsonify({'error': 'Datos requeridos'}), 400

            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            if not email or not password:
                return jsonify({'error': 'Email y contraseña requeridos'}), 400

            usuario = Usuario.query.filter_by(email=email, activo=True).first()
            
            if not usuario:
                return jsonify({'error': 'Credenciales inválidas'}), 401

            # Verificar contraseña
            password_valid = False
            
            if usuario.password_hash and check_password_hash(usuario.password_hash, password):
                password_valid = True
            elif hasattr(usuario, 'temp_password') and usuario.temp_password == password:
                password_valid = True
            
            if not password_valid:
                return jsonify({'error': 'Credenciales inválidas'}), 401

            # Actualizar último acceso
            usuario.ultimo_acceso = datetime.utcnow()
            db.session.commit()

            user_data = {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol,
                'password_changed': usuario.password_changed or False
            }

            return jsonify({
                'success': True,
                'user': user_data,
                'message': 'Login exitoso'
            }), 200
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/auth/login"})
            return jsonify({'error': 'Error interno del servidor'}), 500

    @app.route('/api/auth/verify', methods=['GET'])
    def verify_user():
        """Verificar que el sistema de usuarios funciona"""
        
        log_request(logger, "/api/auth/verify")
        
        try:
            if not database_available or not db:
                return jsonify({'error': 'Base de datos no disponible'}), 503

            # Contar usuarios activos
            total_users = Usuario.query.filter_by(activo=True).count()
            
            return jsonify({
                'status': 'OK',
                'message': 'Sistema de usuarios funcionando',
                'total_active_users': total_users
            }), 200
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/auth/verify"})
            return jsonify({'error': str(e)}), 500

    # ===== ENDPOINT DE SALUD =====
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint para monitoreo mejorado"""
        
        log_request(logger, "/health")
        
        try:
            # Status general de la aplicación
            app_status = 'healthy'

            # Status específico de base de datos
            db_status = 'connected' if database_available else 'disconnected'

            # Información adicional para debugging
            response = {
                'status': app_status,
                'timestamp': datetime.utcnow().isoformat(),
                'database': db_status,
                'database_url_configured': bool(database_url),
                'sqlalchemy_initialized': db is not None
            }

            # Si la BD no está disponible, devolver 503 
            if not database_available:
                response['status'] = 'degraded'
                return jsonify(response), 503

            return jsonify(response), 200

        except Exception as e:
            log_error(logger, e, {"endpoint": "/health"})
            return jsonify({
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }), 500

    # ===== ENDPOINTS DE DISPONIBILIDADES =====
    
    @app.route('/api/disponibilidades', methods=['GET'])
    def get_disponibilidades():
        """Endpoint REST para consultar disponibilidades - Versión mejorada con AvailabilityService"""
        
        log_request(logger, "/api/disponibilidades")
        
        try:
            if not database_available or not db:
                return jsonify({
                    'success': False,
                    'error': 'Base de datos no disponible',
                    'disponibilidades_por_fecha': {},
                    'domos_disponibles': []
                }), 503
            
            # Obtener parámetros
            fecha_inicio = request.args.get('fecha_inicio')
            fecha_fin = request.args.get('fecha_fin')
            domo_especifico = request.args.get('domo')
            personas = request.args.get('personas', type=int)
            
            # Usar AvailabilityService si está disponible
            if availability_service:
                resultado = availability_service.consultar_disponibilidades(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    domo_especifico=domo_especifico,
                    personas=personas
                )
                return jsonify(resultado), 200
            else:
                # Fallback a implementación básica
                disponibilidades = {
                    'success': True,
                    'available_domos': ['Antares', 'Polaris', 'Sirius', 'Centaury'],
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                    'availability_status': 'available',
                    'source': 'fallback_basic'
                }
                return jsonify(disponibilidades), 200
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/disponibilidades"})
            return jsonify({
                'success': False,
                'error': str(e),
                'disponibilidades_por_fecha': {},
                'domos_disponibles': []
            }), 500

    @app.route('/api/agente/disponibilidades', methods=['POST'])
    def agente_consultar_disponibilidades():
        """Endpoint especializado para consultas del agente IA - Versión mejorada"""
        
        log_request(logger, "/api/agente/disponibilidades")
        
        try:
            if not database_available or not db:
                return jsonify({
                    'respuesta_agente': 'Lo siento, no puedo consultar las disponibilidades en este momento. La base de datos no está disponible.',
                    'tiene_disponibilidad': False
                }), 503
            
            data = request.get_json()
            consulta = data.get('consulta', '') if data else ''
            
            if not consulta:
                return jsonify({
                    'respuesta_agente': 'Por favor proporciona una consulta de disponibilidad.',
                    'tiene_disponibilidad': False
                }), 400
            
            # Usar AvailabilityService si está disponible
            if availability_service:
                # Detectar intención primero
                intencion = availability_service.detectar_intencion_consulta(consulta)
                
                if intencion['es_consulta_disponibilidad']:
                    # Procesar consulta natural
                    respuesta_natural = availability_service.consultar_disponibilidades_natural(consulta)
                    
                    # Extraer parámetros para metadatos
                    parametros = availability_service.extraer_parametros_consulta(consulta)
                    
                    return jsonify({
                        'respuesta_agente': respuesta_natural,
                        'tiene_disponibilidad': 'disponible' in respuesta_natural.lower() and 'no tenemos' not in respuesta_natural.lower(),
                        'parametros_detectados': parametros,
                        'intencion_detectada': intencion,
                        'source': 'availability_service',
                        'timestamp': datetime.utcnow().isoformat()
                    }), 200
                else:
                    return jsonify({
                        'respuesta_agente': 'Tu consulta no parece estar relacionada con disponibilidades. ¿Podrías ser más específico sobre fechas o domos?',
                        'tiene_disponibilidad': False,
                        'intencion_detectada': intencion
                    }), 200
            else:
                # Fallback a respuesta básica
                respuesta = {
                    'respuesta_agente': 'Tenemos disponibilidad en nuestros domos. ¿Podrías especificar fechas?',
                    'tiene_disponibilidad': True,
                    'consulta_procesada': consulta,
                    'source': 'fallback_basic'
                }
                return jsonify(respuesta), 200
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/agente/disponibilidades"})
            return jsonify({
                'respuesta_agente': 'Lo siento, ocurrió un error al consultar las disponibilidades. Por favor inténtalo de nuevo.',
                'tiene_disponibilidad': False,
                'error_tecnico': str(e)
            }), 500

    logger.info("Rutas API centralizadas registradas exitosamente",
               extra={"phase": "startup", "component": "api_routes", 
                      "endpoints_count": 16})
    
    return app
# Rutas API modulares usando DatabaseService
# Demuestra cómo reemplazar endpoints existentes con el servicio centralizado

from flask import request, jsonify
from utils.logger import get_logger, log_request, log_response, log_error

# Inicializar logger para este módulo
logger = get_logger(__name__)

def register_api_routes(app, database_service):
    """
    Registrar rutas API modulares usando DatabaseService
    
    Args:
        app: Instancia de Flask
        database_service: Instancia de DatabaseService
    """
    
    if not database_service:
        logger.warning("DatabaseService no disponible, no se registran rutas API",
                      extra={"phase": "startup", "component": "api_routes"})
        return
    
    # ===== ENDPOINTS DE RESERVAS =====
    
    @app.route('/api/v2/reservas', methods=['GET'])
    def get_reservas_v2():
        """Obtener todas las reservas - Versión modular"""
        
        log_request(logger, "/api/v2/reservas")
        
        try:
            success, reservas_data, error = database_service.get_all_reservas()
            
            if success:
                response = {
                    'success': True,
                    'count': len(reservas_data),
                    'reservas': reservas_data
                }
                return jsonify(response), 200
            else:
                response = {
                    'success': False,
                    'error': error,
                    'reservas': []
                }
                return jsonify(response), 503
                
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/v2/reservas"})
            return jsonify({
                'success': False,
                'error': 'Error interno del servidor',
                'reservas': []
            }), 500
    
    @app.route('/api/v2/reservas/stats', methods=['GET'])
    def get_reservas_stats_v2():
        """Obtener estadísticas de reservas - Versión modular"""
        
        log_request(logger, "/api/v2/reservas/stats")
        
        try:
            success, stats_data, error = database_service.get_reservas_stats()
            
            if success:
                return jsonify(stats_data), 200
            else:
                return jsonify({"error": error}), 500
                
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/v2/reservas/stats"})
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/v2/reservas', methods=['POST'])
    def create_reserva_v2():
        """Crear nueva reserva - Versión modular"""
        
        log_request(logger, "/api/v2/reservas")
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Datos requeridos'}), 400
            
            success, reserva_id, error = database_service.create_reserva(data)
            
            if success:
                response = {
                    'success': True,
                    'message': 'Reserva creada exitosamente',
                    'reserva_id': reserva_id
                }
                return jsonify(response), 201
            else:
                response = {
                    'success': False,
                    'error': error
                }
                return jsonify(response), 400
                
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/v2/reservas", "method": "POST"})
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v2/reservas/<int:reserva_id>', methods=['PUT'])
    def update_reserva_v2(reserva_id):
        """Actualizar reserva existente - Versión modular"""
        
        log_request(logger, f"/api/v2/reservas/{reserva_id}")
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Datos requeridos'}), 400
            
            success, error = database_service.update_reserva(reserva_id, data)
            
            if success:
                return jsonify({'message': 'Reserva actualizada exitosamente'}), 200
            else:
                return jsonify({'error': error}), 404 if 'no encontrada' in error else 400
                
        except Exception as e:
            log_error(logger, e, {"endpoint": f"/api/v2/reservas/{reserva_id}", "method": "PUT"})
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v2/reservas/<int:reserva_id>', methods=['DELETE'])
    def delete_reserva_v2(reserva_id):
        """Eliminar reserva - Versión modular"""
        
        log_request(logger, f"/api/v2/reservas/{reserva_id}")
        
        try:
            success, error = database_service.delete_reserva(reserva_id)
            
            if success:
                return jsonify({'message': 'Reserva eliminada exitosamente'}), 200
            else:
                return jsonify({'error': error}), 404 if 'no encontrada' in error else 400
                
        except Exception as e:
            log_error(logger, e, {"endpoint": f"/api/v2/reservas/{reserva_id}", "method": "DELETE"})
            return jsonify({'error': str(e)}), 500
    
    # ===== ENDPOINTS DE USUARIOS =====
    
    @app.route('/api/v2/usuarios', methods=['GET'])
    def get_usuarios_v2():
        """Obtener lista de usuarios - Versión modular"""
        
        log_request(logger, "/api/v2/usuarios")
        
        try:
            include_passwords = request.args.get('include_passwords', 'false').lower() == 'true'
            usuarios = database_service.get_all_users(include_passwords)
            
            return jsonify(usuarios), 200
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/v2/usuarios"})
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v2/usuarios', methods=['POST'])
    def create_usuario_v2():
        """Crear nuevo usuario - Versión modular"""
        
        log_request(logger, "/api/v2/usuarios")
        
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'Datos requeridos'}), 400
            
            nombre = data.get('nombre')
            email = data.get('email')
            rol = data.get('rol', 'limitado')
            
            if not nombre or not email:
                return jsonify({'error': 'Nombre y email son requeridos'}), 400
            
            success, user_data, error = database_service.create_user(nombre, email, rol=rol)
            
            if success:
                response = {
                    'success': True,
                    'id': user_data['id'],
                    'nombre': user_data['nombre'],
                    'temp_password': user_data['temp_password']
                }
                return jsonify(response), 201
            else:
                return jsonify({'error': error}), 400
                
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/v2/usuarios", "method": "POST"})
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/v2/usuarios/<int:user_id>', methods=['PUT'])
    def update_usuario_v2(user_id):
        """Actualizar usuario - Versión modular"""
        
        log_request(logger, f"/api/v2/usuarios/{user_id}")
        
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'Datos requeridos'}), 400
            
            nombre = data.get('nombre')
            email = data.get('email')
            rol = data.get('rol')
            activo = data.get('activo', True)
            
            if not nombre or not email or not rol:
                return jsonify({'error': 'Nombre, email y rol son requeridos'}), 400
            
            success, error = database_service.update_user(user_id, nombre, email, rol, activo)
            
            if success:
                return jsonify({'success': True, 'message': 'Usuario actualizado'}), 200
            else:
                return jsonify({'error': error}), 404 if 'no encontrado' in error else 400
                
        except Exception as e:
            log_error(logger, e, {"endpoint": f"/api/v2/usuarios/{user_id}", "method": "PUT"})
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/v2/usuarios/<int:user_id>', methods=['DELETE'])
    def delete_usuario_v2(user_id):
        """Eliminar usuario - Versión modular"""
        
        log_request(logger, f"/api/v2/usuarios/{user_id}")
        
        try:
            success, error = database_service.delete_user(user_id)
            
            if success:
                return jsonify({'success': True, 'message': 'Usuario eliminado'}), 200
            else:
                return jsonify({'error': error}), 404 if 'no encontrado' in error else 400
                
        except Exception as e:
            log_error(logger, e, {"endpoint": f"/api/v2/usuarios/{user_id}", "method": "DELETE"})
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/v2/auth/login', methods=['POST'])
    def login_v2():
        """Login de usuario - Versión modular"""
        
        log_request(logger, "/api/v2/auth/login")
        
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'Datos requeridos'}), 400
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            if not email or not password:
                return jsonify({'error': 'Email y contraseña requeridos'}), 400
            
            user_data = database_service.authenticate_user(email, password)
            
            if user_data:
                response = {
                    'success': True,
                    'user': user_data,
                    'message': 'Login exitoso'
                }
                return jsonify(response), 200
            else:
                return jsonify({'error': 'Credenciales inválidas'}), 401
                
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/v2/auth/login"})
            return jsonify({'error': 'Error interno del servidor'}), 500
    
    @app.route('/api/v2/usuarios/<int:user_id>/regenerate-password', methods=['POST'])
    def regenerate_password_v2(user_id):
        """Regenerar contraseña para un usuario - Versión modular"""
        
        log_request(logger, f"/api/v2/usuarios/{user_id}/regenerate-password")
        
        try:
            success, new_password, error = database_service.regenerate_user_password(user_id)
            
            if success:
                response = {
                    'success': True,
                    'temp_password': new_password,
                    'message': 'Contraseña regenerada exitosamente'
                }
                return jsonify(response), 200
            else:
                return jsonify({'error': error}), 404 if 'no encontrado' in error else 400
                
        except Exception as e:
            log_error(logger, e, {"endpoint": f"/api/v2/usuarios/{user_id}/regenerate-password"})
            return jsonify({'error': str(e)}), 400
    
    # ===== ENDPOINT DE SALUD =====
    
    @app.route('/api/v2/health', methods=['GET'])
    def health_check_v2():
        """Health check mejorado - Versión modular"""
        
        log_request(logger, "/api/v2/health")
        
        try:
            health_data = database_service.get_database_health()
            
            status_code = 200 if health_data['status'] == 'healthy' else 503
            return jsonify(health_data), status_code
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/api/v2/health"})
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    logger.info("Rutas API modulares registradas exitosamente",
               extra={"phase": "startup", "component": "api_routes", "version": "v2"})
    
    return app
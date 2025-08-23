# Chat REST API routes for agente glamping
# Extracted from agente.py and uses unified conversation service

from flask import request, jsonify
import uuid
from utils.logger import get_logger, log_request, log_response, log_error

# Inicializar logger para este módulo
logger = get_logger(__name__)

# Import unified conversation service
from services.conversation_service import process_chat_conversation


def register_chat_routes(app, user_memories, user_states, load_user_memory, save_user_memory,
                        is_greeting_message, get_welcome_menu, is_menu_selection, 
                        handle_menu_selection, handle_availability_request, parse_reservation_details,
                        validate_and_process_reservation_data, calcular_precio_reserva, db, Reserva,
                        save_reservation_to_pinecone, tools, initialize_agent_safe, run_agent_safe,
                        qa_chains):
    """
    Register chat REST API routes
    
    This function maintains backward compatibility by accepting all dependencies
    that the original chat function needs from agente.py
    """
    
    @app.route("/chat", methods=["POST"])
    def chat():
        data = request.get_json()
        user_input = data.get("input", "").strip()
        session_id = data.get("session_id", str(uuid.uuid4()))


        if not user_input:
            return jsonify({"error": "Falta el campo 'input'"}), 400

        # Process conversation using unified service
        try:
            response_data = process_chat_conversation(
                user_input=user_input,
                session_id=session_id,
                user_memories=user_memories,
                user_states=user_states,
                load_user_memory_func=load_user_memory,
                save_user_memory_func=save_user_memory,
                is_greeting_message_func=is_greeting_message,
                get_welcome_menu_func=get_welcome_menu,
                is_menu_selection_func=is_menu_selection,
                handle_menu_selection_func=handle_menu_selection,
                handle_availability_request_func=handle_availability_request,
                parse_reservation_details_func=parse_reservation_details,
                validate_and_process_reservation_data_func=validate_and_process_reservation_data,
                calcular_precio_reserva_func=calcular_precio_reserva,
                db=db,
                Reserva=Reserva,
                save_reservation_to_pinecone_func=save_reservation_to_pinecone,
                tools=tools,
                initialize_agent_safe_func=initialize_agent_safe,
                run_agent_safe_func=run_agent_safe,
                qa_chains=qa_chains
            )
            
            return jsonify(response_data)
            
        except Exception as e:
            log_error(logger, e, {"endpoint": "/chat", "session_id": session_id})
            return jsonify({
                "session_id": session_id,
                "response": "Lo siento, ocurrió un error procesando tu solicitud. Por favor, intenta de nuevo.",
                "memory": []
            }), 500
    
    return app
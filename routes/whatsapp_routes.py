# WhatsApp webhook routes for agente glamping
# Extracted from agente.py to improve code organization
# Now uses unified conversation service

from flask import request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import uuid
from utils.logger import get_logger, log_request, log_response, log_error

# Inicializar logger para este módulo
logger = get_logger(__name__)

# Import unified conversation service
from services.conversation_service import (
    handle_greeting_new_conversation,
    handle_menu_selection_unified,
    handle_availability_request_unified,
    detect_reservation_intent,
    initiate_reservation_flow,
    process_reservation_step_1,
    process_reservation_step_2,
    process_ai_agent
)

def register_whatsapp_routes(app, db, user_memories, user_states, tools, qa_chains, 
                           load_user_memory, save_user_memory, is_greeting_message,
                           get_welcome_menu, is_menu_selection, handle_menu_selection,
                           handle_availability_request, parse_reservation_details,
                           validate_and_process_reservation_data, calcular_precio_reserva,
                           Reserva, save_reservation_to_pinecone, initialize_agent_safe,
                           run_agent_safe):
    """
    Register WhatsApp webhook routes
    
    This function maintains backward compatibility by accepting all dependencies
    that the original whatsapp_webhook function needs from agente.py
    """
    
    @app.route("/whatsapp_webhook", methods=["POST"])
    def whatsapp_webhook():
        incoming_msg = request.values.get('Body', '').strip()
        from_number = request.values.get('From', '')
        button_payload = request.values.get('ButtonPayload')

        log_request(logger, "/whatsapp_webhook", from_number, incoming_msg)

        resp = MessagingResponse()
        agent_answer = "Lo siento, no pude procesar tu solicitud en este momento."

        # Initialize user memory and state
        if from_number not in user_memories:
            user_memories[from_number] = load_user_memory(from_number)
        if from_number not in user_states:
            user_states[from_number] = {"current_flow": "none", "reserva_step": 0, "reserva_data": {}, "waiting_for_availability": False}
                
        memory = user_memories[from_number]
        user_state = user_states[from_number]

        # 1. Handle greeting in new conversation
        handled, response = handle_greeting_new_conversation(
            memory, incoming_msg, is_greeting_message, get_welcome_menu, save_user_memory, from_number
        )
        if handled:
            resp.message(response)
            return str(resp)
        
        # 2. Handle menu selection
        handled, response = handle_menu_selection_unified(
            incoming_msg, user_state, memory, qa_chains, handle_menu_selection, 
            save_user_memory, from_number, is_menu_selection
        )
        if handled:
            if isinstance(response, dict):
                resp.message(response["message"])
            else:
                resp.message(response)
            return str(resp)

        # 3. Handle availability request
        handled, response = handle_availability_request_unified(
            incoming_msg, user_state, memory, handle_availability_request, 
            save_user_memory, from_number
        )
        if handled:
            resp.message(response)
            return str(resp)

        # 4. Handle reservation flow
        if user_state["current_flow"] == "none" and detect_reservation_intent(incoming_msg, button_payload):
            response = initiate_reservation_flow(user_state, memory, save_user_memory, from_number)
            resp.message(response)
            return str(resp)
        
        # 5. Process reservation step 1 (data collection)
        if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 1:
            resp.message("🔄 Procesando tu solicitud de reserva, por favor espera un momento...")
            response = process_reservation_step_1(
                incoming_msg, user_state, memory, save_user_memory, from_number,
                parse_reservation_details, validate_and_process_reservation_data, calcular_precio_reserva
            )
            resp.message(response)
            return str(resp)

        # 6. Process reservation step 2 (confirmation)
        if user_state["current_flow"] == "reserva" and user_state["reserva_step"] == 2:
            response = process_reservation_step_2(
                incoming_msg, user_state, memory, save_user_memory, from_number,
                db, Reserva, calcular_precio_reserva, save_reservation_to_pinecone
            )
            resp.message(response)
            return str(resp)

        # 7. Process through AI agent (default case)
        agent_answer = process_ai_agent(
            incoming_msg, memory, tools, initialize_agent_safe, run_agent_safe, 
            save_user_memory, from_number
        )
        
        resp.message(agent_answer)
        logger.info(f"WhatsApp respuesta enviada a {from_number}", extra={"user_id": from_number, "response_preview": agent_answer[:100], "phase": "response"})
        return str(resp)
    
    return app
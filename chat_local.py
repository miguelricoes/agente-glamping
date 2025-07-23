import requests
import json

print("Escribe 'salir' para terminar.\n")

# Variable para almacenar el ID de sesión. Inicialmente es None.
current_session_id = None

while True:
    mensaje = input("Tú: ")
    if mensaje.lower() in ["salir", "exit"]:
        break

    # Prepara el 'payload' (cuerpo de la solicitud JSON)
    payload = {"input": mensaje}

    # Si ya tenemos un session_id, lo añadimos al payload
    if current_session_id:
        payload["session_id"] = current_session_id

    try:
        # Envía la solicitud POST a tu aplicación Flask
        res = requests.post("http://127.0.0.1:8080/chat", json=payload)
        res.raise_for_status() # Esto lanzará un error si la respuesta es 4xx o 5xx

        response_data = res.json()

        # Si es la primera interacción y el servidor nos envió un session_id, lo guardamos
        if current_session_id is None and "session_id" in response_data:
            current_session_id = response_data["session_id"]
            print(f"(DEBUG) Sesión iniciada con ID: {current_session_id}\n") # Mensaje opcional para depuración

        print("Maria:", response_data.get("response"))
        # Puedes mantener o eliminar esta línea según si quieres ver la memoria en la consola
        # print("🧠 Memoria actual:", json.dumps(response_data.get("memory"), ensure_ascii=False, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Error al comunicarse con el servidor: {e}")
    except json.JSONDecodeError:
        print("Error: La respuesta del servidor no es un JSON válido.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

print("Conversación terminada.")
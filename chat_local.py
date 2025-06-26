import requests

print("Escribe 'salir' para terminar.\n")

while True:
    mensaje = input("Tú: ")
    if mensaje.lower() in ["salir", "exit"]:
        break
    try:
        res = requests.post("http://127.0.0.1:8080/chat", json={"input": mensaje})
        print("Agente:", res.json().get("response"))
    except Exception as e:
        print(" Error:", e)

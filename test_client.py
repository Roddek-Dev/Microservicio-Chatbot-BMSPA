import requests
import json

# URL base del microservicio
BASE_URL = "http://localhost:8000"

def test_health():
    """Probar endpoint de salud"""
    response = requests.get(f"{BASE_URL}/health")
    print("=== HEALTH CHECK ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_question(question):
    """Probar una pregunta al chatbot"""
    payload = {"question": question}
    response = requests.post(
        f"{BASE_URL}/ask",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    
    print(f"=== PREGUNTA: {question} ===")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Respuesta: {result['answer']}")
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    # Probar salud del servicio
    test_health()
    
    # Preguntas de prueba
    preguntas_prueba = [
        "¿Cuáles son los horarios de las sucursales?",
        "¿Qué servicios de barbería ofrecen?",
        "¿Cómo puedo agendar una cita en la app?",
        "¿En qué ciudades tienen sucursales?",
        "¿Puedo pagar con tarjeta de crédito?",
        "¿Cuánto cuesta un corte de cabello?",  # Esta debería dar respuesta de "no tengo información"
        "¿Cómo cancelo una cita?"
    ]
    
    for pregunta in preguntas_prueba:
        test_question(pregunta)
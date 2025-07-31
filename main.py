"""
Microservicio de Chatbot FAQ para BarberMusic&Spa
Desarrollado con FastAPI y Google Gemini
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización de FastAPI
app = FastAPI(
    title="BMSPA FAQ Chatbot",
    description="Microservicio de chatbot para preguntas frecuentes de BarberMusic&Spa",
    version="1.0.0"
)

# Configuración de Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)

# Configuración del modelo Gemini según especificaciones
GENERATION_CONFIG = GenerationConfig(
    temperature=0.2,
    max_output_tokens=150,
    top_p=0.95,
    stop_sequences=["."]
)

# Inicialización del modelo
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=GENERATION_CONFIG
)

# Modelos Pydantic para request y response
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Pregunta del usuario")

class AnswerResponse(BaseModel):
    answer: str = Field(..., description="Respuesta del chatbot")

# Contexto base de conocimiento del chatbot
KNOWLEDGE_BASE = """
CONTEXTO 1: RESUMEN DE LA EMPRESA (BarberMusic&Spa)
- Modelo de Negocio: Es un negocio híbrido que funciona como una red de franquicias.
- Combina una barbería tradicional, un spa de servicio completo y un centro de estética médica.
- Su estrategia es ser un "todo en uno" para el cuidado personal.
- Público Objetivo: Se dirige tanto a hombres (con servicios de barbería) como a mujeres (con una amplia gama de servicios de spa y estética).
- Ubicaciones: Tiene sucursales en varias ciudades de México, como Villahermosa, San Luis Potosí y Mérida.
- Todas sus tiendas están ubicadas estratégicamente en plazas comerciales de alto tráfico.
- Horarios: Todas las sucursales tienen un horario estandarizado: Lunes a Domingo, de 11:00 a.m. a 9:00 p.m.
- Cartera de Servicios: Muy amplia. Incluye:
  * Barbería: Cortes de cabello, arreglos de barba, afeitados.
  * Salón y Spa: Manicuras, pedicuras, balayage, keratina, depilación, masajes, tratamientos faciales.
  * Medspa: Tratamientos avanzados como Criolipólisis (eliminación de grasa) y Radiofrecuencia (estiramiento de piel).
- Presencia Digital: La empresa no tiene una página web oficial ni redes sociales propias.
- Toda su presencia online y sistema de citas se gestiona a través de la plataforma de terceros Fresha.

CONTEXTO 2: FUNCIONALIDADES DE LA APP DE CLIENTE (Flutter)
- Objetivo de la App: Permitir a los clientes agendar citas, comprar productos y gestionar su perfil.
- Autenticación: Los usuarios pueden registrarse e iniciar sesión con email y contraseña. El acceso a la app requiere un token de seguridad.
- Pantalla de Inicio: Muestra un saludo, un botón grande para "Agendar Nueva Cita", promociones y servicios populares.
- Flujo de Agendar Cita: Es un proceso guiado paso a paso:
  1. Selección de Servicio: El usuario elige un único servicio de una lista.
  2. Selección de Sucursal: Elige la tienda a la que desea asistir.
  3. Selección de Fecha y Hora: Un calendario muestra los días y horarios disponibles.
  4. Selección de Personal (Opcional): Puede elegir un empleado específico o "Cualquiera".
  5. Resumen y Confirmación: Revisa todos los detalles y confirma la cita. El pago se realiza en la sucursal.
- Tienda: Permite comprar productos de cuidado personal. Tiene un carrito de compras. El pago se puede realizar con PayPal y MercadoPago.
- Mis Citas: Una sección para ver citas futuras y pasadas. Permite cancelar citas próximas y dejar reseñas de citas pasadas.
- Mis Órdenes: Un historial de las compras de productos realizadas.
- Perfil: Muestra la información del usuario. Permite editar el perfil, gestionar la dirección de envío y cerrar sesión.
"""

# Prompt del sistema para el chatbot
SYSTEM_PROMPT = f"""
Eres un asistente virtual amigable y profesional para BarberMusic&Spa (BMSPA). Tu función es responder preguntas frecuentes sobre la empresa y ayudar a los usuarios con la aplicación móvil.

REGLAS IMPORTANTES:
1. Solo puedes usar la información del contexto proporcionado
2. Responde de manera concisa, amigable y profesional
3. Si no tienes información sobre el tema preguntado, responde amablemente que no tienes esa información
4. No inventes URLs, números de teléfono ni detalles que no estén en el contexto
5. No puedes realizar acciones como agendar citas por el usuario
6. Enfócate en responder sobre servicios, horarios, ubicaciones y funcionalidades de la app

CONTEXTO DE CONOCIMIENTO:
{KNOWLEDGE_BASE}

Responde siempre en español de manera clara y directa.
"""

def generate_response(question: str) -> str:
    """
    Genera una respuesta usando Google Gemini basada en la pregunta del usuario
    
    Args:
        question (str): Pregunta del usuario
        
    Returns:
        str: Respuesta generada por el chatbot
    """
    try:
        # Crear el prompt completo
        full_prompt = f"{SYSTEM_PROMPT}\n\nPregunta del usuario: {question}\n\nRespuesta:"
        
        # Generar respuesta con Gemini
        response = model.generate_content(full_prompt)
        
        # Extraer el texto de la respuesta
        if response.text:
            answer = response.text.strip()
            
            # Validar que la respuesta no esté vacía
            if not answer:
                return "No tengo información sobre ese tema, pero puedo ayudarte con preguntas sobre nuestros servicios, horarios o cómo usar la aplicación."
            
            return answer
        else:
            logger.warning("Gemini returned empty response")
            return "No tengo información sobre ese tema, pero puedo ayudarte con preguntas sobre nuestros servicios, horarios o cómo usar la aplicación."
            
    except Exception as e:
        logger.error(f"Error generating response with Gemini: {str(e)}")
        return "Lo siento, no puedo procesar tu pregunta en este momento. Por favor, intenta de nuevo."

@app.get("/")
async def root():
    """Endpoint de salud del servicio"""
    return {"message": "BMSPA FAQ Chatbot is running", "status": "healthy"}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Endpoint principal para procesar preguntas del chatbot
    
    Args:
        request (QuestionRequest): Objeto con la pregunta del usuario
        
    Returns:
        AnswerResponse: Respuesta del chatbot
    """
    try:
        logger.info(f"Processing question: {request.question}")
        
        # Validar que la pregunta no esté vacía
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
        
        # Generar respuesta usando Gemini
        answer = generate_response(request.question)
        
        logger.info(f"Generated answer: {answer}")
        
        return AnswerResponse(answer=answer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ask_question: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno del servidor. Por favor, intenta de nuevo."
        )

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio"""
    try:
        # Verificar que Gemini esté configurado correctamente
        test_response = model.generate_content("Test")
        return {
            "status": "healthy",
            "gemini_status": "connected" if test_response else "disconnected",
            "service": "BMSPA FAQ Chatbot"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "gemini_status": "disconnected",
            "service": "BMSPA FAQ Chatbot",
            "error": str(e)
        }

# Configuración adicional para producción
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
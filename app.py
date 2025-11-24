from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from google import genai
import gunicorn # Importamos gunicorn para el servidor de producción

# ----------------------------------------------
# 1. Configuración Inicial y Carga de API Key
# ----------------------------------------------

# Cargar variables de entorno (como la API Key de Gemini)
# Esto es útil para desarrollo local, pero en Render usaremos variables de entorno directas.
load_dotenv()
app = Flask(__name__)

# Intentamos obtener la clave de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. Inicializar el cliente de Gemini
try:
    if not GEMINI_API_KEY:
        # En Render, la clave se leerá automáticamente si se configura como variable de entorno.
        # Si no está en .env, intentará usar el token que ya deberías haber configurado en tu VM.
        # Para el despliegue, la API Key es OBLIGATORIA.
        print("Advertencia: No se encontró la variable GEMINI_API_KEY. Asegúrate de configurarla en Render.")
    
    # Inicializar el cliente con la clave (si está disponible)
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error al inicializar el cliente Gemini: {e}")
    # En un entorno real, manejarías este error para evitar que la aplicación se caiga.

# ----------------------------------------------
# 3. La Ruta Principal del Webhook
# ----------------------------------------------
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Función que maneja las peticiones POST de Dialogflow.
    Recibe el mensaje del usuario y llama a la API de Gemini.
    """
    try:
        # Extraer el JSON enviado por Dialogflow
        req = request.get_json()
        
        # El mensaje del usuario viene en queryText dentro de queryResult
        user_message = req.get('queryResult', {}).get('queryText', 'Mensaje vacío')

        # Si el mensaje está vacío (algo raro), devolvemos un error
        if not user_message:
            return jsonify({
                "fulfillmentMessages": [{"text": {"text": ["Lo siento, no pude entender el mensaje."]}}]
            })

        # ----------------------------------------------
        # 4. Prompting y Llamada a Gemini
        # ----------------------------------------------
        
        # Prompt base para controlar el comportamiento del bot
        system_prompt = (
            "Eres un profesor de IA divertido y claro, especializado en GenAI. "
            "Explica todo como si le hablaras a un principiante curioso."
        )

        # Llamada a la API de Google Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config={
                "system_instruction": system_prompt, # Establecemos el rol del bot
                "temperature": 0.7                   # Control de creatividad (0.0 es muy determinista)
            }
        )

        # La respuesta de Gemini se extrae del atributo .text
        answer = response.text

        # ----------------------------------------------
        # 5. Devolver Respuesta a Dialogflow
        # ----------------------------------------------
        
        # El formato de respuesta que Dialogflow espera para el texto
        return jsonify({
            "fulfillmentMessages": [
                {"text": {"text": [answer]}}
            ]
        })

    except Exception as e:
        # Manejo de errores (ej. fallo en la conexión a Gemini)
        error_message = f"Error interno del servidor al procesar la solicitud: {str(e)}"
        print(error_message) # Imprimir en logs para debugging
        return jsonify({
            "fulfillmentMessages": [
                {"text": {"text": [f"Ups! Parece que hay un problema técnico: {str(e)}"]}}
            ]
        })

# ----------------------------------------------
# 6. Ejecución Local (Opcional, pero útil para probar)
# ----------------------------------------------
if __name__ == "__main__":
    # Cuando lo ejecutas con 'python app.py', se usa esto.
    # En producción (Render), gunicorn se encarga de la ejecución.
    print("Ejecutando la aplicación localmente en http://127.0.0.1:5000/webhook")
    app.run(port=5000, debug=True)

FROM python:3.11-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo de dependencias e instalamos todo
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código (app.py, etc.)
COPY . .

# Comando para iniciar el servidor con Gunicorn
# Gunicorn es el servidor de producción que se usa en la nube para correr Flask.
# El comando 'gunicorn' debe apuntar a tu archivo:app y a la instancia de la aplicación:
# --bind 0.0.0.0:8080 : Render requiere que se escuche en el puerto 8080
# app:app          : "app" es el nombre del módulo (app.py) y "app" es la instancia de Flask dentro del módulo.
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 app:app

# Apartado 2.11a: escucha por MQTT la telemetría del robot-02, en vivo,
# y guarda cada mensaje en Elasticsearch, en el índice fabrica-vivo-telemetria.
# No termina solo: sigue escuchando hasta que lo pares con Ctrl + C.
#
# Uso: python 11a-cargar-vivo-mqtt.py
# (con la planta en marcha: docker compose up -d, en la carpeta del simulador)

import json

import paho.mqtt.client as mqtt
from elasticsearch import Elasticsearch

# Leemos la configuración de configuracion.py (está en esta misma carpeta)
from configuracion import ES_URL, ES_USUARIO, ES_CONTRASENA, ES_CERTIFICADO

# Índice para lo que llega en vivo: aparte del histórico, porque es distinto para cada uno.
INDICE = "fabrica-vivo-telemetria"

# Servidor MQTT del simulador. Si arrancaste la planta con otro puerto
# (MQTT_PUERTO=11883 docker compose up -d), cambia aquí 1883 por ese puerto.
MQTT_SERVIDOR = "localhost"
MQTT_PUERTO = 1883

# Topic al que nos suscribimos: solo la telemetría del robot-02.
TOPIC = "fabrica/L1/robot-02/telemetria"

# 1. Creamos el cliente de Elasticsearch, igual que en los demás scripts.
es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USUARIO, ES_CONTRASENA),
    ca_certs=ES_CERTIFICADO,
)

# Contador de mensajes recibidos, para mostrarlo en pantalla.
recibidos = 0


# 2. Lo que hay que hacer en cada momento lo escribimos en dos funciones.
#    No las llamamos nosotros: se las damos al cliente MQTT, y él las llama
#    cuando pasa algo (por eso se llaman «callbacks», funciones de vuelta).

# Se llama cuando el cliente se conecta al servidor MQTT.
# Nos suscribimos aquí, y no antes, porque si la conexión se corta y se recupera,
# el cliente vuelve a llamar a esta función y la suscripción se repite.
def al_conectar(cliente, datos_usuario, flags, codigo, propiedades):
    print("Conectado al servidor MQTT:", codigo)
    cliente.subscribe(TOPIC)
    print("Escuchando", TOPIC, "(para parar, Ctrl + C)")


# Se llama cada vez que llega un mensaje.
def al_recibir(cliente, datos_usuario, mensaje):
    # global: vamos a cambiar el contador, que está fuera de la función.
    global recibidos

    # El contenido del mensaje (payload) es un texto JSON: lo convertimos en un diccionario.
    documento = json.loads(mensaje.payload)

    # El mismo identificador que en el histórico: equipo y hora.
    id_documento = documento["equipo"] + "_" + documento["ts"]

    # Lo enviamos a Elasticsearch, uno a uno, según llegan.
    es.index(index=INDICE, id=id_documento, document=documento)

    recibidos += 1
    print(recibidos, documento["ts"], documento["estado"])


# 3. Creamos el cliente MQTT, le damos las dos funciones y lo conectamos.
#    CallbackAPIVersion.VERSION2 indica qué forma tienen nuestras funciones
#    (la de la versión 2 de paho-mqtt).
cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.on_connect = al_conectar
cliente.on_message = al_recibir
cliente.connect(MQTT_SERVIDOR, MQTT_PUERTO)

# 4. Nos quedamos escuchando para siempre. Con Ctrl + C, Python lanza
#    KeyboardInterrupt: lo capturamos para terminar sin un mensaje de error.
try:
    cliente.loop_forever()
except KeyboardInterrupt:
    cliente.disconnect()
    print("Parado. Mensajes recibidos:", recibidos)

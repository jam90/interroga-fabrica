# Apartado 2.5: carga en Elasticsearch la telemetría de robot-02 (una muestra por minuto),
# en lotes con bulk. Como los datos no traen un identificador, lo construimos con el equipo y la hora.
#
# Uso: python 05-cargar-telemetria.py

import json

from elasticsearch import Elasticsearch, helpers

# Leemos la configuración de configuracion.py (está en esta misma carpeta)
from configuracion import ES_URL, ES_USUARIO, ES_CONTRASENA, ES_CERTIFICADO, DATOS

# Nombre del índice donde guardaremos la telemetría.
# Aquí irán varios equipos: robot-02 ahora y cnc-01 más adelante, con Logstash.
INDICE = "fabrica-telemetria"

# Equipo que vamos a cargar
EQUIPO = "robot-02"

# 1. Creamos el cliente, igual que en los scripts anteriores.
es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USUARIO, ES_CONTRASENA),
    ca_certs=ES_CERTIFICADO,
)

# 2. Buscamos los ficheros de telemetría del equipo: uno por día, con nombres como 2026-09-23.jsonl.
#    Ojo: el nombre lleva la fecha local de la planta, y el campo ts de dentro, la hora UTC.
carpeta = DATOS / "L1" / EQUIPO / "telemetria"
ficheros = sorted(carpeta.glob("*.jsonl"))
print("Ficheros de telemetría en", carpeta, ":", len(ficheros))
if not ficheros:
    print("  ERROR: no hay ficheros. Revisa DATOS en configuracion.py y que hayas generado el histórico")
    exit(1)

# 3. Recorremos los ficheros. De cada uno preparamos un lote con todas sus muestras
#    y se lo damos a bulk, igual que con las inspecciones.
total = 0
for fichero in ficheros:
    lote = []
    with open(fichero, encoding="utf-8") as f:
        for linea in f:
            # Saltamos las líneas vacías, si las hay
            if not linea.strip():
                continue

            # Convertimos la línea (texto) en un diccionario de Python
            documento = json.loads(linea)

            # Construimos el identificador: equipo y hora, por ejemplo robot-02_2026-09-23T07:00:00.000Z.
            #  - Es único: un equipo envía una sola muestra por minuto.
            #  - Es estable: la misma muestra tiene siempre el mismo, en cada carga.
            #  - Lleva el equipo porque en este índice habrá varios, y dos equipos
            #    pueden enviar una muestra a la misma hora.
            identificador = documento["equipo"] + "_" + documento["ts"]

            accion = {
                "_index": INDICE,
                "_id": identificador,
                "_source": documento,
            }
            lote.append(accion)

    # Enviamos el lote, igual que en 04-cargar-inspecciones.py
    guardados, errores = helpers.bulk(es, lote)
    print(" ", fichero.name, "->", guardados, "documentos")
    total += guardados

print("Documentos enviados:", total)

# 4. Pedimos a Elasticsearch cuántos documentos tiene el índice.
es.indices.refresh(index=INDICE)
recuento = es.count(index=INDICE)["count"]
print("Documentos en el índice", INDICE, ":", recuento)

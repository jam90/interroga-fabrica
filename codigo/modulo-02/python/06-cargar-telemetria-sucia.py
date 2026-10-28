# Apartado 2.6: carga en Elasticsearch, tal cual, la telemetría SUCIA de robot-02,
# para ver qué pasa con cada defecto. Es una copia de 05-cargar-telemetria.py:
# solo cambian la carpeta de los datos y el índice.
#
# Uso: python 06-cargar-telemetria-sucia.py

import json

from elasticsearch import Elasticsearch, helpers

# Leemos la configuración de configuracion.py (está en esta misma carpeta)
from configuracion import ES_URL, ES_USUARIO, ES_CONTRASENA, ES_CERTIFICADO, DATOS

# Índice de práctica: no empieza por fabrica- para no mezclarlo con los datos buenos.
INDICE = "practica-telemetria-sucia"

# Equipo que vamos a cargar
EQUIPO = "robot-02"

# 1. Creamos el cliente, igual que en los scripts anteriores.
es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USUARIO, ES_CONTRASENA),
    ca_certs=ES_CERTIFICADO,
)

# 2. Buscamos los ficheros de telemetría del equipo en datos-sucios, que está junto a datos.
#    DATOS.parent es la carpeta que contiene a DATOS (la del simulador).
#    Además de un fichero por día, hay uno llamado fecha-desconocida.jsonl.
carpeta = DATOS.parent / "datos-sucios" / "L1" / EQUIPO / "telemetria"
ficheros = sorted(carpeta.glob("*.jsonl"))
print("Ficheros de telemetría en", carpeta, ":", len(ficheros))
if not ficheros:
    print("  ERROR: no hay ficheros. Revisa DATOS en configuracion.py y que hayas generado el dato sucio")
    exit(1)

# 3. Recorremos los ficheros. De cada uno preparamos un lote con todas sus muestras
#    y se lo damos a bulk, igual que en 05-cargar-telemetria.py.
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

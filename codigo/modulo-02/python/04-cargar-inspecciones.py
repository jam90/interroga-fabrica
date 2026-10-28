# Apartado 2.4: carga en Elasticsearch las inspecciones de calidad (una por pieza),
# en lotes con bulk y con la pieza como identificador, para poder repetir la carga sin duplicar.
#
# Uso: python 04-cargar-inspecciones.py

import json

from elasticsearch import Elasticsearch, helpers

# Leemos la configuración de configuracion.py (está en esta misma carpeta)
from configuracion import ES_URL, ES_USUARIO, ES_CONTRASENA, ES_CERTIFICADO, DATOS

# Nombre del índice donde guardaremos las inspecciones.
# Si no existe, Elasticsearch lo crea solo al recibir el primer lote.
INDICE = "fabrica-inspecciones"

# 1. Creamos el cliente, igual que en los scripts anteriores.
es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USUARIO, ES_CONTRASENA),
    ca_certs=ES_CERTIFICADO,
)

# 2. Buscamos los ficheros de inspecciones: uno por día, con nombres como 2026-09-23.jsonl.
carpeta = DATOS / "L1" / "calidad-01" / "inspecciones"
ficheros = sorted(carpeta.glob("*.jsonl"))
print("Ficheros de inspecciones en", carpeta, ":", len(ficheros))
if not ficheros:
    print("  ERROR: no hay ficheros. Revisa DATOS en configuracion.py y que hayas generado el histórico")
    exit(1)

# 3. Recorremos los ficheros. De cada uno preparamos un lote con todas sus piezas
#    y se lo damos a bulk, que lo envía en pocas peticiones grandes (de 500 en 500 documentos),
#    en lugar de una petición por pieza.
total = 0
for fichero in ficheros:
    # El lote es una lista. Cada elemento dice dónde va el documento y con qué identificador.
    lote = []
    with open(fichero, encoding="utf-8") as f:
        for linea in f:
            # Saltamos las líneas vacías, si las hay
            if not linea.strip():
                continue

            # Convertimos la línea (texto) en un diccionario de Python
            documento = json.loads(linea)

            # Preparamos la acción para bulk:
            #  - "_index": el índice donde va el documento.
            #  - "_id": su identificador. Usamos pieza_id, que es único para cada pieza.
            #    Si un documento llega con un _id que ya existe, Elasticsearch lo sustituye
            #    en lugar de añadir otro: así, repetir la carga no duplica nada.
            #  - "_source": el documento en sí.
            accion = {
                "_index": INDICE,
                "_id": documento["pieza_id"],
                "_source": documento,
            }
            lote.append(accion)

    # Enviamos el lote. helpers.bulk devuelve cuántos documentos se han guardado bien
    # y la lista de errores, que aquí siempre está vacía: si algún documento falla,
    # bulk para el script con un error (BulkIndexError) que dice cuál y por qué.
    guardados, errores = helpers.bulk(es, lote)
    print(" ", fichero.name, "->", guardados, "documentos")
    total += guardados

print("Documentos enviados:", total)

# 4. Pedimos a Elasticsearch cuántos documentos tiene el índice.
#    Antes, refresh() hace que los documentos recién llegados ya se puedan contar.
es.indices.refresh(index=INDICE)
recuento = es.count(index=INDICE)["count"]
print("Documentos en el índice", INDICE, ":", recuento)

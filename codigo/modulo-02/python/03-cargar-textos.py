# Apartado 2.3: carga en Elasticsearch los textos de la planta
# (partes de mantenimiento y notas de turno), documento a documento.
#
# Uso: python 03-cargar-textos.py

import json

from elasticsearch import Elasticsearch

# Leemos la configuración de configuracion.py (está en esta misma carpeta)
from configuracion import ES_URL, ES_USUARIO, ES_CONTRASENA, ES_CERTIFICADO, DATOS

# Nombre del índice donde guardaremos los textos.
# Si no existe, Elasticsearch lo crea solo al recibir el primer documento.
INDICE = "fabrica-textos"

# 1. Creamos el cliente, igual que en 02-probar-conexion.py.
es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USUARIO, ES_CONTRASENA),
    ca_certs=ES_CERTIFICADO,
)

# 2. Buscamos los ficheros de textos: uno por día, con nombres como 2026-09-23.jsonl.
#    sorted() los ordena por nombre, que aquí es lo mismo que ordenarlos por fecha.
carpeta = DATOS / "L1" / "textos"
ficheros = sorted(carpeta.glob("*.jsonl"))
print("Ficheros de textos en", carpeta, ":", len(ficheros))
if not ficheros:
    print("  ERROR: no hay ficheros. Revisa DATOS en configuracion.py y que hayas generado el histórico")
    exit(1)

# 3. Recorremos los ficheros y, dentro de cada uno, sus líneas.
#    En un fichero JSONL, cada línea es un documento JSON completo.
total = 0
for fichero in ficheros:
    cargados = 0
    with open(fichero, encoding="utf-8") as f:
        for linea in f:
            # Saltamos las líneas vacías, si las hay
            if not linea.strip():
                continue

            # Convertimos la línea (texto) en un diccionario de Python
            documento = json.loads(linea)

            # Enviamos el documento a Elasticsearch: una petición por documento.
            # No le damos un identificador, así que Elasticsearch le pone uno al azar.
            es.index(index=INDICE, document=documento)
            cargados += 1

    print(" ", fichero.name, "->", cargados, "documentos")
    total += cargados

print("Documentos enviados:", total)

# 4. Pedimos a Elasticsearch cuántos documentos tiene el índice.
#    Antes, refresh() hace que los documentos recién llegados ya se puedan contar
#    (si no, Elasticsearch los cuenta al cabo de un segundo, más o menos).
es.indices.refresh(index=INDICE)
recuento = es.count(index=INDICE)["count"]
print("Documentos en el índice", INDICE, ":", recuento)

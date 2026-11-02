# Apartado 3.5: lanza desde Python una consulta nested de Dev Tools.
# Busca las piezas con la garganta de soldadura fuera de tolerancia
# del 21 al 23 de septiembre y muestra, de cada una, la hora y la medida que falló.
#
# Uso: python 05-consultar.py

from datetime import datetime
from zoneinfo import ZoneInfo

from elasticsearch import Elasticsearch

# Leemos la configuración de configuracion.py (la copiaste del módulo 2 a esta carpeta)
from configuracion import ES_URL, ES_USUARIO, ES_CONTRASENA, ES_CERTIFICADO

INDICE = "fabrica-inspecciones"

# Zona horaria de la planta: para mostrar las horas como las ve un operario.
ZONA = ZoneInfo("Europe/Madrid")

# 1. Creamos el cliente, igual que en los scripts del módulo 2.
es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USUARIO, ES_CONTRASENA),
    ca_certs=ES_CERTIFICADO,
)

# 2. La consulta, escrita como un diccionario de Python.
#    Es la misma que lanzaste en Dev Tools: compárala con la guía.
#    Lo único que cambia es la sintaxis: True/False y comillas de Python en lugar de JSON.
consulta = {
    "bool": {
        "filter": [
            {"range": {"ts": {"gte": "2026-09-21", "lt": "2026-09-24", "time_zone": "Europe/Madrid"}}},
            {
                "nested": {
                    "path": "medidas",
                    "query": {
                        "bool": {
                            "filter": [
                                {"term": {"medidas.cota": "garganta_soldadura"}},
                                {"term": {"medidas.resultado": "NOK"}},
                            ]
                        }
                    },
                    # inner_hits: que nos diga también qué medida ha coincidido
                    "inner_hits": {},
                }
            },
        ]
    }
}

# 3. Lanzamos la búsqueda. Pedimos hasta 100 piezas (son menos), ordenadas por hora,
#    y solo los campos que vamos a usar.
respuesta = es.search(
    index=INDICE,
    query=consulta,
    sort=[{"ts": "asc"}],
    size=100,
    source=["pieza_id", "ts"],
)

# 4. Recorremos los resultados. Cada uno es un diccionario, como los que ves en Dev Tools.
total = respuesta["hits"]["total"]["value"]
print("Piezas con la garganta de soldadura NOK del 21 al 23:", total)
print()

piezas_por_dia = {}
for resultado in respuesta["hits"]["hits"]:
    pieza = resultado["_source"]

    # ts viene en UTC, como texto (2026-09-21T04:42:07.218Z).
    # Lo pasamos a la hora de la planta para mostrarlo.
    hora_utc = datetime.fromisoformat(pieza["ts"])
    hora_local = hora_utc.astimezone(ZONA)

    # La medida que coincidió con la consulta está en inner_hits.
    medida = resultado["inner_hits"]["medidas"]["hits"]["hits"][0]["_source"]
    # Límites de la tolerancia: el nominal más o menos lo que se admite
    minimo = medida["nominal"] + medida["tol_min"]
    maximo = medida["nominal"] + medida["tol_max"]

    print(hora_local.strftime("%d/%m %H:%M"), pieza["pieza_id"],
          "| garganta:", medida["valor"], medida["unidad"], "| admitido:", round(minimo, 2), "a", round(maximo, 2))

    # Contamos las piezas de cada día
    dia = hora_local.strftime("%d/%m")
    piezas_por_dia[dia] = piezas_por_dia.get(dia, 0) + 1

# 5. Resumen por día
print()
for dia, cuantas in piezas_por_dia.items():
    print("Día", dia, ":", cuantas, "piezas")

# Apartado 2.6: limpia la telemetría sucia de robot-02 y la carga en Elasticsearch.
# Corrige las fechas mal formadas, quita los valores absurdos (atípicos), cuenta los nulos
# y descarta los duplicados. Al final escribe un resumen de lo que ha hecho.
#
# Uso: python 06-limpiar-telemetria.py

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from elasticsearch import Elasticsearch, helpers

# Leemos la configuración de configuracion.py (está en esta misma carpeta)
from configuracion import ES_URL, ES_USUARIO, ES_CONTRASENA, ES_CERTIFICADO, DATOS

# Índice de práctica donde guardaremos la telemetría ya limpia
INDICE = "practica-telemetria-limpia"

# Equipo que vamos a limpiar
EQUIPO = "robot-02"

# Zona horaria de la planta: la necesitamos para corregir las fechas en hora local
ZONA_PLANTA = ZoneInfo("Europe/Madrid")

# Rangos de valores posibles para cada tipo de medida: (mínimo, máximo).
# Son límites físicos razonables para este robot, no los valores habituales:
# lo que quede fuera es imposible y, por tanto, un error del dato.
RANGO_PORCENTAJE = (0, 100)     # override_pct, en %
RANGO_CICLO = (0, 120)          # ciclo_s: duración del ciclo, en segundos
RANGO_CORRIENTE = (0, 15)       # corriente_ejeN_a, en amperios
RANGO_TEMPERATURA = (0, 120)    # temp_motor_ejeN_c, en grados
RANGO_POTENCIA = (0, 10)        # potencia_kw, en kilovatios

# 1. Creamos el cliente, igual que en los scripts anteriores.
es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USUARIO, ES_CONTRASENA),
    ca_certs=ES_CERTIFICADO,
)

# 2. Buscamos los ficheros de la telemetría sucia (incluido fecha-desconocida.jsonl).
carpeta = DATOS.parent / "datos-sucios" / "L1" / EQUIPO / "telemetria"
ficheros = sorted(carpeta.glob("*.jsonl"))
print("Ficheros de telemetría sucia en", carpeta, ":", len(ficheros))
if not ficheros:
    print("  ERROR: no hay ficheros. Revisa DATOS en configuracion.py y que hayas generado el dato sucio")
    exit(1)

# Contadores para el resumen final
leidas = 0
fechas_corregidas = 0
atipicos_quitados = 0
nulos_encontrados = 0
duplicados_descartados = 0

# Identificadores ya vistos, para descartar los duplicados.
# Un set es una colección sin repetidos en la que se comprueba muy rápido si algo ya está.
vistos = set()

# Aquí guardaremos las acciones para bulk: esta vez, todas en un solo lote,
# porque las muestras de fecha-desconocida.jsonl son de días distintos.
lote = []

# 3. Recorremos los ficheros y limpiamos cada muestra.
for fichero in ficheros:
    with open(fichero, encoding="utf-8") as f:
        for linea in f:
            if not linea.strip():
                continue
            documento = json.loads(linea)
            leidas += 1

            # 3.1. Fechas. Las buenas están en UTC y acaban en Z: 2026-09-23T10:00:00.000Z.
            #      Las malas vienen en hora local y sin zona: 23/09/2026 12:00:00.
            ts = documento["ts"]
            if not ts.endswith("Z"):
                # Leemos la fecha con su formato (día/mes/año hora:minuto:segundo)...
                fecha_local = datetime.strptime(ts, "%d/%m/%Y %H:%M:%S")
                # ...le decimos que es hora de la planta...
                fecha_local = fecha_local.replace(tzinfo=ZONA_PLANTA)
                # ...la pasamos a UTC...
                fecha_utc = fecha_local.astimezone(ZoneInfo("UTC"))
                # ...y la escribimos igual que las buenas.
                documento["ts"] = fecha_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                fechas_corregidas += 1

            # 3.2. Duplicados. El identificador es el mismo que en el apartado 2.5.
            #      Con él, Elasticsearch ya los sustituiría, pero así los contamos y no los enviamos.
            identificador = documento["equipo"] + "_" + documento["ts"]
            if identificador in vistos:
                duplicados_descartados += 1
                continue
            vistos.add(identificador)

            # 3.3. Atípicos y nulos: revisamos cada medida.
            valores = documento["valores"]
            for nombre in valores:
                valor = valores[nombre]

                # Los nulos se quedan como están: no nos inventamos el dato. Solo los contamos.
                if valor is None:
                    nulos_encontrados += 1
                    continue

                # Elegimos el rango según el nombre de la medida.
                # Las que no están aquí (programa, modo, ciclos_total...) no se revisan.
                if nombre == "override_pct":
                    rango = RANGO_PORCENTAJE
                elif nombre == "ciclo_s":
                    rango = RANGO_CICLO
                elif nombre.startswith("corriente_"):
                    rango = RANGO_CORRIENTE
                elif nombre.startswith("temp_motor_"):
                    rango = RANGO_TEMPERATURA
                elif nombre == "potencia_kw":
                    rango = RANGO_POTENCIA
                else:
                    continue

                # Si el valor está fuera del rango, es imposible: lo dejamos vacío (None),
                # igual que un nulo. Mejor un hueco que un dato falso.
                minimo, maximo = rango
                if valor < minimo or valor > maximo:
                    valores[nombre] = None
                    atipicos_quitados += 1

            lote.append({
                "_index": INDICE,
                "_id": identificador,
                "_source": documento,
            })

# 4. Enviamos el lote con bulk.
guardados, errores = helpers.bulk(es, lote)

# 5. Resumen de la limpieza
print("Líneas leídas:", leidas)
print("  Fechas corregidas:", fechas_corregidas)
print("  Duplicados descartados:", duplicados_descartados)
print("  Atípicos quitados:", atipicos_quitados)
print("  Nulos encontrados (se dejan vacíos):", nulos_encontrados)
print("Documentos enviados:", guardados)

es.indices.refresh(index=INDICE)
recuento = es.count(index=INDICE)["count"]
print("Documentos en el índice", INDICE, ":", recuento)

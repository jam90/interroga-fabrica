# Apartado 2.2: comprueba que Python puede conectarse a Elasticsearch
# y que encuentra los datos del simulador.
#
# Uso: python 02-probar-conexion.py

from elasticsearch import Elasticsearch

# Leemos la configuración de configuracion.py (está en esta misma carpeta)
from configuracion import ES_URL, ES_USUARIO, ES_CONTRASENA, ES_CERTIFICADO, DATOS

# 1. Comprobamos que existe el certificado.
#    Sin él, Python no puede comprobar que habla con tu Elasticsearch.
print("Certificado:", ES_CERTIFICADO)
if not ES_CERTIFICADO.exists():
    print("  ERROR: no encuentro el certificado. Revisa ES_CERTIFICADO en configuracion.py")
    exit(1)
print("  OK")

# 2. Creamos el cliente: el objeto con el que hablaremos con Elasticsearch.
#    Le damos la dirección, el usuario y la contraseña, y el certificado.
es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USUARIO, ES_CONTRASENA),
    ca_certs=ES_CERTIFICADO,
)

# 3. Le pedimos a Elasticsearch su información básica.
#    Es lo mismo que hiciste con curl en el apartado 2.1.
print("Elasticsearch:", ES_URL)
info = es.info()
print("  OK. Versión:", info["version"]["number"], "| Nodo:", info["name"])

# 4. Le pedimos el estado del clúster (lo mismo que GET _cluster/health en Kibana).
salud = es.cluster.health()
print("  Estado del clúster:", salud["status"], "| Nodos:", salud["number_of_nodes"])

# 5. Comprobamos que encontramos los datos del simulador.
print("Datos del simulador:", DATOS)
if not DATOS.exists():
    print("  ERROR: no encuentro la carpeta. Revisa DATOS en configuracion.py")
    exit(1)
textos = sorted((DATOS / "L1" / "textos").glob("*.jsonl"))
print("  OK. Ficheros de textos:", len(textos))

print()
print("Todo listo para cargar datos.")

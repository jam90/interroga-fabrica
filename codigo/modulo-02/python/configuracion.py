# Configuración común a todos los scripts de Python del módulo 2.
#
# Antes de usar los scripts, cambia aquí la contraseña del usuario elastic
# (la que te dio Elasticsearch al arrancar por primera vez).
# Si has instalado las cosas en otras carpetas, cambia también las rutas.
#
# Este fichero es solo para tu ordenador: no lo compartas, porque lleva tu contraseña.

from pathlib import Path

# --- Conexión con Elasticsearch ---

# Dirección de Elasticsearch. Con la seguridad activada, siempre https.
ES_URL = "https://localhost:9200"

# Usuario y contraseña.
ES_USUARIO = "elastic"
ES_CONTRASENA = "escribe-aqui-tu-contrasena"

# Certificado que creó Elasticsearch al arrancar por primera vez.
# Path.home() es tu carpeta personal (en Linux, /home/tu-usuario).
# En Windows, si lo instalaste en C:\elk, pon: Path("C:/elk/elasticsearch-9.5.5/config/certs/http_ca.crt")
ES_CERTIFICADO = Path.home() / "elk" / "elasticsearch-9.5.5" / "config" / "certs" / "http_ca.crt"

# --- Datos del simulador ---

# Carpeta con el histórico de 30 días que generaste en el módulo 1.
# En Windows, si lo descomprimiste en C:\cursos, pon: Path("C:/cursos/simulador-planta/datos")
DATOS = Path.home() / "cursos" / "simulador-planta" / "datos"

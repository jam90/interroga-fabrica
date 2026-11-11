# Interroga a tu fábrica — código de las prácticas

Código del curso «Interroga a tu fábrica» (Tknika, departamento de IA): ingesta de datos de planta en Elasticsearch con Python y Logstash, *mappings* y, más adelante, un sistema RAG que responde preguntas sobre esos datos.

Las guías de cada práctica están en el Moodle del curso. Allí se indica qué fichero de este repositorio se usa en cada paso.

## Contenido

```
codigo/
├── modulo-02/
│   ├── python/      # scripts de carga (histórico y en vivo por MQTT)
│   └── logstash/    # pipelines de Logstash (.conf y pipelines.yml)
└── modulo-03/
    ├── kibana/      # panel de Kibana ya hecho, para importarlo si te atascas
    ├── mappings/    # mappings explícitos de los índices fabrica-*
    └── python/      # consultas desde Python
```

Los ficheros llevan delante el número del apartado en el que se usan (`04-cargar-inspecciones.py` → apartado 2.4).

## Requisitos

- Elasticsearch, Kibana y Logstash **9.5.5** (paquetes de la web de Elastic, sin Docker).
- Python 3.12 o posterior.
- El simulador de planta, que genera los datos: <https://github.com/jam90/simulador-planta>.

## Preparación

El curso supone esta estructura de carpetas:

```
~/cursos/
├── codigo/              # este repositorio (la carpeta codigo/)
└── simulador-planta/    # el simulador
~/elk/
├── elasticsearch-9.5.5/
├── kibana-9.5.5/
└── logstash-9.5.5/
```

Entorno de Python:

```bash
cd ~/cursos/codigo/modulo-02/python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Después, edita `configuracion.py` con tu contraseña del usuario `elastic` (y las rutas, si no usas las de arriba). Es el único fichero que hay que tocar.

## Licencia

- **Código:** MIT (ver `LICENSE`).
- **Documentación** (este README): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.es).

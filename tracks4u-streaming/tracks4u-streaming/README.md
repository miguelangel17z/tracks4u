# Ingesta en streaming — tracks4u

Pipeline extremo a extremo (según `AGENTS/contrato.md` §8):

    Django Outbox (telemetry_event)
      -> GET /api/events/drain/ + POST /api/events/ack/ (producer.py)
      -> Kafka (topic tracks4u.events en 127.0.0.1:9092)
      -> consumer.py
      -> CSV en S3 zona RAW

Ruta en S3 (bucket por defecto en la EC2 `tracks4u-app`):

    s3://tracks4u-datalake-463790652932-us-east-1/raw/entity=play_events/ingest_date=AAAA-MM-DD/events_<timestamp>.csv

El `producer.py` opera por defecto como **conector Outbox → Kafka** con entrega *at-least-once*:
1. Consulta lotes confirmables desde `GET {DJANGO_URL}/api/events/drain/?since=<cursor>&limit=<DRAIN_LIMIT>` autenticándose con `Authorization: Bearer <TELEMETRY_DRAIN_TOKEN>`.
2. Normaliza cada evento al esquema de columnas de `consumer.py` (`event_id, ts, session_id, user_id, event_type, track_id, device, geo, entrypoint, payload`) y lo publica en `tracks4u.events` usando `session_id` como clave de partición.
3. Ejecuta `p.flush()`, comprueba que no quedaron mensajes pendientes ni errores de entrega en Kafka y **solo entonces** confirma el lote en `POST {DJANGO_URL}/api/events/ack/` con `{"last_id": next_cursor}`.

El `consumer.py` lee de `tracks4u.events`, valida `event_id`, deduplica en memoria por `event_id` y escribe un archivo CSV cada 100 eventos o cada 10 segundos en `datalake/` y lo sube a S3.

## Archivos
- `docker-compose.yml` : levanta Kafka (un solo nodo, imagen `apache/kafka`, puerto `127.0.0.1:9092`)
- `producer.py`        : conector Outbox Django → Kafka (o simulador aleatorio si `SIMULATE=1`)
- `consumer.py`        : lee de Kafka, escribe CSV en `datalake/` y los sube a S3 (`s3://tracks4u-datalake-463790652932-us-east-1/raw/entity=play_events/`)
- `requirements.txt`   : `confluent-kafka`, `boto3`, `requests`

## Infraestructura configurada en la EC2 `tracks4u-app`
- **Directorio en la EC2:** `~/tracks4u-streaming`
- **Broker Kafka:** `127.0.0.1:9092` (corriendo en la misma EC2 `tracks4u-app`)
- **Topic Kafka:** `tracks4u.events`
- **Bucket S3 (con IAM Role adjunto a la EC2):** `tracks4u-datalake-463790652932-us-east-1` (`us-east-1`)
- **Destino RAW del consumer:** `s3://tracks4u-datalake-463790652932-us-east-1/raw/entity=play_events/`
- **Backend Django local en la EC2:** `http://127.0.0.1:8000`

## Ejecución en la EC2 (`~/tracks4u-streaming`)

1. Verificar que Kafka está arriba (o levantarlo):

       cd ~/tracks4u-streaming
       docker compose up -d
       docker ps        # debe aparecer apache/kafka en 9092

2. Crear/activar el entorno virtual e instalar dependencias:

       python3 -m venv venv
       source venv/bin/activate
       pip install -r requirements.txt

3. **Terminal 1 — consumer** (usa por defecto `S3_BUCKET=tracks4u-datalake-463790652932-us-east-1` y `AWS_DEFAULT_REGION=us-east-1` mediante el IAM Role de la EC2):

       cd ~/tracks4u-streaming
       source venv/bin/activate
       python consumer.py

4. **Terminal 2 — producer (modo conector real con Django Outbox)**:

       cd ~/tracks4u-streaming
       source venv/bin/activate
       TELEMETRY_DRAIN_TOKEN=<token_del_env_de_django> DJANGO_URL=http://127.0.0.1:8000 python producer.py

5. **Modo simulador (opcional, para probar Kafka -> S3 sin depender de Django)**:

       cd ~/tracks4u-streaming
       source venv/bin/activate
       SIMULATE=1 python producer.py

## Cómo comprobar que funciona
- El conector (`producer.py`) imprime al drenar lotes del outbox:
      Drenados y confirmados 12 eventos (acked=12, cursor=0 -> 12)
- El `consumer.py` imprime al volcar lotes a disco y S3:
      Guardados 12 eventos en datalake/raw/... -> s3://tracks4u-datalake-463790652932-us-east-1/raw/entity=play_events/ingest_date=.../events_....csv
- En S3:
      aws s3 ls s3://tracks4u-datalake-463790652932-us-east-1/raw/entity=play_events/ --recursive

## Variables de entorno

### `producer.py`
| Variable | Default | Descripción |
|---|---|---|
| `TELEMETRY_DRAIN_TOKEN` | *(obligatorio en modo conector)* | Token Bearer configurado en `tracks4u/.env` para `/api/events/drain/` y `/api/events/ack/`. |
| `DJANGO_URL` | `http://127.0.0.1:8000` | URL base del backend Django. |
| `BOOTSTRAP` | `127.0.0.1:9092` | Dirección del broker Kafka. |
| `KAFKA_TOPIC` | `tracks4u.events` | Topic destino en Kafka. |
| `DRAIN_LIMIT` | `500` | Tamaño máximo de lote por petición de drenaje. |
| `POLL_SECONDS` | `3` | Segundos de espera cuando no hay eventos nuevos. |
| `SIMULATE` | `0` | Si es `1`, genera eventos sintéticos aleatorios sin consultar Django. |

### `consumer.py`
| Variable | Default | Descripción |
|---|---|---|
| `S3_BUCKET` | `tracks4u-datalake-463790652932-us-east-1` | Bucket S3 donde se suben los CSV de `raw/entity=play_events/`. |
| `AWS_DEFAULT_REGION` | `us-east-1` | Región de AWS para `boto3`. |
| `BOOTSTRAP` | `127.0.0.1:9092` | Dirección del broker Kafka. |
| `KAFKA_TOPIC` | `tracks4u.events` | Topic de Kafka suscrito. |
| `LOCAL_ONLY` | `0` | Si es `1`, guarda únicamente en `datalake/` local sin subir a S3. |

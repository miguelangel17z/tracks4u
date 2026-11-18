# Ingesta en streaming — tracks4u (`tracks4u-streaming`)

Pipeline extremo a extremo (según `AGENTS/contrato.md` §8):

    Django Outbox (tabla telemetry_event en RDS)
      -> GET /api/events/drain/ + POST /api/events/ack/ (producer.py)
      -> Kafka (topic tracks4u.events)
      -> consumer.py
      -> CSV en S3 zona RAW (s3://tracks4u-datalake-463790652932-us-east-1/raw/entity=play_events/)

Ruta en S3:

    s3://tracks4u-datalake-463790652932-us-east-1/raw/entity=play_events/ingest_date=AAAA-MM-DD/events_<timestamp>.csv

---

## Cómo funciona la integración Django ↔ Kafka

1. **`producer.py` (Conector Outbox → Kafka):**
   - Hace polling a `GET {DJANGO_URL}/api/events/drain/?since=<cursor>&limit=<DRAIN_LIMIT>` con la cabecera `Authorization: Bearer <TELEMETRY_DRAIN_TOKEN>`.
   - Adapta cada evento a las 10 columnas de `consumer.py` (`event_id, ts, session_id, user_id, event_type, track_id, device, geo, entrypoint, payload`) y lo publica al topic `tracks4u.events` con clave `session_id`.
   - Ejecuta `p.flush()`, verifica que haya 0 mensajes pendientes y 0 errores en Kafka, y **solo entonces** confirma con `POST {DJANGO_URL}/api/events/ack/` (`{"last_id": next_cursor}`).
   - Si se ejecuta con `SIMULATE=1`, funciona como simulador de eventos aleatorios sin consultar a Django.
2. **`consumer.py` (Kafka → CSV → S3 RAW):**
   - Se suscribe a `tracks4u.events`, deduplica por `event_id` y cada 100 eventos o 10 segundos guarda un CSV en `datalake/raw/entity=play_events/ingest_date=YYYY-MM-DD/` y lo sube a `s3://tracks4u-datalake-463790652932-us-east-1/raw/entity=play_events/` usando el IAM Role de la EC2.

---

## Escenario 1: Django corre en una EC2 y Kafka corre en otra EC2 (`tracks4u-app`)

### Opción 1A (Recomendada): Correr `producer.py` y `consumer.py` en la EC2 de Kafka (`tracks4u-app`) apuntando al HTTP de la EC2 de Django

Con esta opción **no necesitas reconfigurar Kafka ni abrir el puerto 9092**, porque `producer.py` y `consumer.py` hablan con Kafka en `127.0.0.1:9092` dentro de `tracks4u-app`.

1. **En el Security Group de la EC2 de Django:**
   Permite tráfico TCP entrante al puerto **`8000`** (o `80` si usas Nginx) desde la **IP privada de la EC2 de Kafka (`tracks4u-app`)**.
2. **En la EC2 de Django:**
   Asegúrate de que `ALLOWED_HOSTS` en `tracks4u/.env` incluya la IP privada de la EC2 de Django (o `*`) y que Django esté corriendo en `0.0.0.0:8000`:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
3. **En la EC2 de Kafka (`tracks4u-app`, carpeta `~/tracks4u-streaming`):**
   Copia los archivos actualizados (`producer.py`, `consumer.py`, `requirements.txt`) e instala dependencias:
   ```bash
   cd ~/tracks4u-streaming
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   - **Terminal 1 (`consumer.py`):**
     ```bash
     cd ~/tracks4u-streaming
     source venv/bin/activate
     AWS_DEFAULT_REGION=us-east-1 \
     S3_BUCKET=tracks4u-datalake-463790652932-us-east-1 \
     BOOTSTRAP=127.0.0.1:9092 \
     python consumer.py
     ```
   - **Terminal 2 (`producer.py` conectándose a la EC2 de Django):**
     ```bash
     cd ~/tracks4u-streaming
     source venv/bin/activate
     DJANGO_URL=http://<IP_PRIVADA_EC2_DJANGO>:8000 \
     TELEMETRY_DRAIN_TOKEN=<MISMO_TOKEN_DEL_ENV_DE_DJANGO> \
     BOOTSTRAP=127.0.0.1:9092 \
     python producer.py
     ```

---

### Opción 1B: Correr `producer.py` en la EC2 de Django y conectarlo por red al Kafka de `tracks4u-app:9092`

Si prefieres ejecutar `producer.py` en la **EC2 de Django** y que publique remotamente al broker Kafka de `tracks4u-app`:

1. **En el Security Group de la EC2 de Kafka (`tracks4u-app`):**
   Permite tráfico TCP entrante al puerto **`9092`** desde la **IP privada (o Security Group) de la EC2 de Django**.
2. **En la EC2 de Kafka (`tracks4u-app`):**
   Reinicia el contenedor de Kafka anunciando la IP privada de `tracks4u-app` en `KAFKA_HOST`:
   ```bash
   cd ~/tracks4u-streaming
   KAFKA_HOST=<IP_PRIVADA_EC2_KAFKA> docker compose up -d
   ```
   Y arranca el `consumer.py` en `tracks4u-app`:
   ```bash
   cd ~/tracks4u-streaming
   source venv/bin/activate
   AWS_DEFAULT_REGION=us-east-1 \
   S3_BUCKET=tracks4u-datalake-463790652932-us-east-1 \
   BOOTSTRAP=<IP_PRIVADA_EC2_KAFKA>:9092 \
   python consumer.py
   ```
3. **En la EC2 de Django:**
   Arranca `producer.py` leyendo de `http://127.0.0.1:8000` (Django local) y produciendo hacia `<IP_PRIVADA_EC2_KAFKA>:9092`:
   ```bash
   cd ~/tracks4uProject/tracks4u-streaming/tracks4u-streaming
   source ../../.venv/bin/activate
   pip install -r requirements.txt

   DJANGO_URL=http://127.0.0.1:8000 \
   TELEMETRY_DRAIN_TOKEN=<MISMO_TOKEN_DEL_ENV_DE_DJANGO> \
   BOOTSTRAP=<IP_PRIVADA_EC2_KAFKA>:9092 \
   python producer.py
   ```

---

## Escenario 2: Django y Kafka corren en la misma EC2 (`tracks4u-app`)

Si ambos corren en `tracks4u-app`, todo usa `127.0.0.1`:

```bash
# Terminal 1 (Consumer)
cd ~/tracks4u-streaming
source venv/bin/activate
python consumer.py

# Terminal 2 (Producer)
cd ~/tracks4u-streaming
source venv/bin/activate
TELEMETRY_DRAIN_TOKEN=<MISMO_TOKEN_DEL_ENV_DE_DJANGO> DJANGO_URL=http://127.0.0.1:8000 python producer.py
```

---

## Variables de entorno

### `producer.py`
| Variable | Default | Descripción |
|---|---|---|
| `TELEMETRY_DRAIN_TOKEN` | *(obligatorio en modo conector)* | Token Bearer configurado en `tracks4u/.env` para `/api/events/drain/` y `/api/events/ack/`. |
| `DJANGO_URL` | `http://127.0.0.1:8000` | URL base del backend Django (`http://<IP_PRIVADA_EC2_DJANGO>:8000` si está en otra EC2). |
| `BOOTSTRAP` | `127.0.0.1:9092` | Dirección del broker Kafka (`<IP_PRIVADA_EC2_KAFKA>:9092` si Kafka está en otra EC2). |
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

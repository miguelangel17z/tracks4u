# Módulo de Recomendación Musical — Tracks4U (Zona ANALYTICS)

Entrena un recomendador colaborativo **Item-Item (similitud coseno)** a partir de los eventos de comportamiento en la zona **RAW** (`raw/entity=play_events/ingest_date=AAAA-MM-DD/*.csv`), lo evalúa con **Hit-Rate@10** frente a un baseline de popularidad y al azar, y escribe los resultados en **Parquet** en la zona **ANALYTICS** de S3 (`s3://tracks4u-datalake-463790652932-us-east-1/analytics/`):

- `analytics/entity=recommendations/ingest_date=AAAA-MM-DD/part-0000.parquet` (`user_id, rank, track_id, score, generated_at`)
- `analytics/entity=user_profile/ingest_date=AAAA-MM-DD/part-0000.parquet` (`user_id, play_start, play_complete, like, playlist_add, purchase_intent, skip, skip_rate`)
- `analytics/entity=model_metrics/ingest_date=AAAA-MM-DD/part-0000.parquet` (`fecha, hit_rate_modelo, hit_rate_popular, azar, n_usuarios, n_canciones, n_eventos`)

---

## Opción 1: Ejecución con Docker Compose en la EC2 (sin afectar Django ni Kafka)

Este módulo está 100% aislado: no expone ni ocupa puertos y usa `network_mode: "host"` para tomar automáticamente las credenciales del IAM Role (`LabRole`) de la EC2 y terminar limpiamente tras publicar los Parquet en S3 y mostrar el reporte de demo:

```bash
cd ~/tracks4uProject
git pull origin main
cd tracks4u-recommender
docker compose up --build
```

Si ya tienes suficientes eventos reales en S3 y no quieres regenerar el CSV sintético:
```bash
GENERATE_SYNTHETIC=0 docker compose up --build
```

---

## Opción 2: Ejecución Directa con Python en la EC2

```bash
cd ~/tracks4uProject/tracks4u-recommender
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export AWS_DEFAULT_REGION=us-east-1
export S3_BUCKET=tracks4u-datalake-463790652932-us-east-1

# 1. Generar dataset sintético con estructura de clusters (200 usuarios, 300 canciones, 10 géneros)
python gen_synthetic.py

# 2. Entrenar modelo Item-Item, evaluar Hit-Rate@10 y publicar Parquet en S3 ANALYTICS
python recommend.py

# 3. Mostrar resumen de filas, métricas y top-5 recomendaciones para la demo
python check_output.py
```

---

## Verificar archivos Parquet en S3

```bash
aws s3 ls s3://tracks4u-datalake-463790652932-us-east-1/analytics/ --recursive
```

---

## Errores Comunes y Solución

1. **`AccessDenied` al leer o listar en S3 (`ListObjectsV2` / `GetObject`):**
   - El IAM Role de la EC2 necesita `s3:GetObject`, `s3:PutObject` y `s3:ListBucket` sobre `arn:aws:s3:::tracks4u-datalake-463790652932-us-east-1` y `arn:aws:s3:::tracks4u-datalake-463790652932-us-east-1/*`. Si falla la lectura de S3, `recommend.py` cae automáticamente a `datalake/raw/` local.
2. **No hay archivos CSV (`No objects to concatenate` en el script base):**
   - `recommend.py` valida si la carpeta/prefijo `raw/entity=play_events/` está vacío y termina limpiamente indicando que primero se ejecute `python gen_synthetic.py` o el `consumer.py` de Kafka.
3. **`Hit-rate@10` cercano al valor aleatorio (`~0.033`):**
   - Ocurre cuando en `raw/entity=play_events/` solo hay eventos del simulador completamente uniforme (`SIMULATE=1`), donde no existe correlación entre usuarios y canciones. Ejecuta `python gen_synthetic.py` (que simula preferencias por 2 clusters de género por usuario) para observar un `Hit-rate@10` del modelo claramente superior al baseline popular y al azar.

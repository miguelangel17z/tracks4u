import csv
import json
import os
import time
from datetime import datetime, timezone

from confluent_kafka import Consumer

DEFAULT_S3_BUCKET = "tracks4u-datalake-463790652932-us-east-1"
DEFAULT_S3_REGION = "us-east-1"

BOOT = os.getenv("BOOTSTRAP", "127.0.0.1:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "tracks4u.events")
REGION = os.getenv("AWS_DEFAULT_REGION", DEFAULT_S3_REGION)
LOCAL_ONLY = os.getenv("LOCAL_ONLY", "").lower() in ("1", "true", "yes")
BUCKET = None if LOCAL_ONLY else os.getenv("S3_BUCKET", DEFAULT_S3_BUCKET)

s3 = None
if BUCKET:
    import boto3

    s3 = boto3.client("s3", region_name=REGION)  # en EC2 usa el IAM Role, no hace falta clave

FIELDS = [
    "event_id",
    "ts",
    "session_id",
    "user_id",
    "event_type",
    "track_id",
    "device",
    "geo",
    "entrypoint",
    "payload",
]
c = Consumer(
    {
        "bootstrap.servers": BOOT,
        "group.id": "raw-writer",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
)
c.subscribe([TOPIC])
seen, buf, last = set(), [], time.time()


def flush():
    global buf, last
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rel = f"raw/entity=play_events/ingest_date={d}/events_{int(time.time()*1000)}.csv"
    path = f"datalake/{rel}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(buf)
    msg = f"Guardados {len(buf)} eventos en {path}"
    if s3:
        try:
            s3.upload_file(path, BUCKET, rel)
            msg += f"  ->  s3://{BUCKET}/{rel}"
        except Exception as e:
            msg += f"  (ERROR subiendo a S3: {e})"
    c.commit()
    print(msg)
    buf, last = [], time.time()


try:
    while True:
        m = c.poll(1.0)
        if m and not m.error():
            try:
                ev = json.loads(m.value())
            except Exception:
                continue
            if not ev.get("event_id") or ev["event_id"] in seen:
                continue
            seen.add(ev["event_id"])
            buf.append({k: ev.get(k) for k in FIELDS})
        if buf and (len(buf) >= 100 or time.time() - last > 10):
            flush()
except KeyboardInterrupt:
    if buf:
        flush()

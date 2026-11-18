from datetime import datetime, timedelta, timezone
import json
import os
import random
import uuid

import pandas as pd

BUCKET = os.getenv("S3_BUCKET", "").strip() or None
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

N_USERS = 200
N_TRACKS = 300
N_CLUSTERS = 10
EVENTS_PER_USER = 45

DEVICES = ["web_desktop", "web_mobile", "web_tablet"]
GEOS = ["Colombia", "Mexico", "Argentina", "Spain"]
ENTRYPOINTS = ["home", "search", "playlist", "track_page", "artist_profile"]
POSITIVE_EVENTS = [
    ("play_start", 0.45),
    ("play_complete", 0.25),
    ("like", 0.14),
    ("playlist_add", 0.10),
    ("purchase_intent", 0.06),
]


def choose_positive_event(rng):
    r = rng.random()
    acc = 0.0
    for ev_type, prob in POSITIVE_EVENTS:
        acc += prob
        if r <= acc:
            return ev_type
    return "play_start"


def main():
    rng = random.Random(42)
    base_ts = datetime.now(timezone.utc) - timedelta(hours=6)

    # 300 canciones divididas en 10 clusters de género (30 canciones por cluster)
    clusters = {
        c: [f"t{c * 30 + i + 1}" for i in range(30)]
        for c in range(N_CLUSTERS)
    }
    all_tracks = [f"t{i + 1}" for i in range(N_TRACKS)]

    rows = []
    for u_idx in range(1, N_USERS + 1):
        user_id = f"u{u_idx}"
        # Cada usuario prefiere 2 clusters de género (80% de sus escuchas positivas)
        fav_clusters = rng.sample(range(N_CLUSTERS), 2)
        fav_pool = clusters[fav_clusters[0]] + clusters[fav_clusters[1]]
        other_pool = [t for t in all_tracks if t not in fav_pool]
        session_id = f"s_{rng.randint(1000, 9999)}"
        device = rng.choice(DEVICES)
        geo = rng.choice(GEOS)

        for step in range(EVENTS_PER_USER):
            ts = (base_ts + timedelta(seconds=u_idx * 15 + step * 20)).isoformat()
            if rng.random() < 0.82:
                track = rng.choice(fav_pool) if rng.random() < 0.80 else rng.choice(other_pool)
                ev_type = choose_positive_event(rng)
            else:
                track = rng.choice(other_pool)
                ev_type = "skip"

            # En ~10% de las filas simulamos el formato real de Django:
            # user_id numérico y track_id dentro del JSON de payload
            if rng.random() < 0.10:
                numeric_track = int(track[1:])
                row_user = str(u_idx)
                row_track = ""
                row_payload = json.dumps({"track_id": numeric_track, "source": "django_outbox"})
            else:
                row_user = user_id
                row_track = track
                row_payload = "{}"

            rows.append(
                {
                    "event_id": str(uuid.uuid4()),
                    "ts": ts,
                    "session_id": session_id,
                    "user_id": row_user,
                    "event_type": ev_type,
                    "track_id": row_track,
                    "device": device,
                    "geo": geo,
                    "entrypoint": rng.choice(ENTRYPOINTS),
                    "payload": row_payload,
                }
            )

    df = pd.DataFrame(rows)
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rel = f"raw/entity=play_events/ingest_date={d}/synthetic_0001.csv"
    path = f"datalake/{rel}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)

    msg = (
        f"Generados {len(df)} eventos sintéticos "
        f"({N_USERS} usuarios, {N_TRACKS} canciones, {N_CLUSTERS} clusters) -> {path}"
    )
    if BUCKET:
        try:
            import boto3

            s3 = boto3.client("s3", region_name=REGION)
            s3.upload_file(path, BUCKET, rel)
            msg += f" y s3://{BUCKET}/{rel}"
        except Exception as exc:
            msg += f" (ADVERTENCIA: falló subida a S3: {exc}; se conserva copia local)"
    print(msg, flush=True)


if __name__ == "__main__":
    main()

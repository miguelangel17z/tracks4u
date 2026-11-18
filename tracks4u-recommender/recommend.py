import ast
from datetime import datetime, timezone
import glob
import io
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

BUCKET = os.getenv("S3_BUCKET", "").strip() or None
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

s3 = None
if BUCKET:
    import boto3

    s3 = boto3.client("s3", region_name=REGION)

# Pesos de negocio por tipo de evento de comportamiento
W = {
    "play_start": 1,
    "play_complete": 3,
    "like": 4,
    "playlist_add": 4,
    "purchase_intent": 5,
    "skip": -2,
}
K = 10

REQUIRED_COLS = [
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


def parse_payload(val):
    """Parsea payload tanto si llega como JSON válido o como dict de Python con comillas simples."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return {}
    if isinstance(val, dict):
        return val
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "{}"):
        return {}
    try:
        parsed = json.loads(s)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass
    try:
        parsed = ast.literal_eval(s)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def normalize_id(val, prefix=""):
    """
    Normaliza IDs numéricos reales de Django (6, 6.0, '6') y sintéticos ('t6', 'u6')
    a un único formato string consistente (ej. 't6' / 'u6') para evitar duplicados.
    """
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "anon", "anonymous"):
        return None
    if s.endswith(".0"):
        s = s[:-2]
    if prefix and s.startswith(prefix) and s[len(prefix) :].isdigit():
        return s
    if s.isdigit():
        return f"{prefix}{s}" if prefix else s
    return s


def load_local_csvs():
    """Lee todos los CSV locales de datalake/raw/entity=play_events/*/*.csv."""
    files = sorted(glob.glob("datalake/raw/entity=play_events/*/*.csv"))
    dfs = []
    for fpath in files:
        try:
            df_part = pd.read_csv(fpath)
            if not df_part.empty:
                dfs.append(df_part)
        except Exception as exc:
            print(f"ADVERTENCIA: Se ignoró archivo local inválido {fpath}: {exc}", flush=True)
    return dfs


def load():
    """
    Lee los CSV de raw/entity=play_events/ desde S3 (si S3_BUCKET está definido)
    o desde datalake/ local. Si no hay archivos o falla el permiso en S3, maneja
    el error con mensajes claros sin caerse con un traceback.
    """
    dfs = []
    if BUCKET and s3 is not None:
        try:
            paginator = s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=BUCKET, Prefix="raw/entity=play_events/"):
                for o in page.get("Contents", []):
                    key = o["Key"]
                    if not key.endswith(".csv") or "/_checks/" in key:
                        continue
                    try:
                        body = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
                        if not body.strip():
                            continue
                        df_part = pd.read_csv(io.BytesIO(body))
                        if not df_part.empty:
                            dfs.append(df_part)
                    except Exception as exc:
                        print(f"ADVERTENCIA: No se pudo leer s3://{BUCKET}/{key}: {exc}", flush=True)
        except Exception as exc:
            print(
                f"ADVERTENCIA: Error listando/leyendo S3 s3://{BUCKET}/raw/entity=play_events/ ({exc}). "
                "Intentando cargar desde datalake/ local...",
                flush=True,
            )
            dfs = load_local_csvs()
    else:
        dfs = load_local_csvs()

    if not dfs:
        origen = (
            f"s3://{BUCKET}/raw/entity=play_events/"
            if BUCKET
            else "datalake/raw/entity=play_events/*/*.csv"
        )
        print(
            f"AVISO: No se encontraron archivos CSV con eventos en {origen}.\n"
            "Sugerencia: ejecuta primero 'python gen_synthetic.py' o el consumer de Kafka.",
            flush=True,
        )
        sys.exit(0)

    return pd.concat(dfs, ignore_index=True)


def clean_events(raw_df):
    """
    Limpia y normaliza eventos reales de Django y sintéticos:
    - Asegura columnas esperadas.
    - Deduplica por event_id.
    - Descarta filas con event_type nulo o ts inválido.
    - Extrae track_id desde payload si la columna track_id viene vacía.
    - Descarta usuarios anónimos (user_id vacío) y normaliza user_id y track_id a string.
    """
    df = raw_df.copy()
    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = None

    # Limpiar event_id y deduplicar
    df = df[df["event_id"].notna()].copy()
    df["event_id"] = df["event_id"].astype(str).str.strip()
    df = df[df["event_id"] != ""].drop_duplicates("event_id")

    # Filtrar event_type válidos para el modelo
    df = df[df["event_type"].notna()].copy()
    df["event_type"] = df["event_type"].astype(str).str.strip()
    df = df[df["event_type"].isin(W)].copy()

    # Validar timestamp (ts)
    parsed_ts = pd.to_datetime(df["ts"], errors="coerce", utc=True)
    df = df[parsed_ts.notna()].copy()

    if df.empty:
        return df

    # Si track_id está vacío en la columna, extraerlo del diccionario payload
    def resolve_track_id(row):
        tid = normalize_id(row.get("track_id"), prefix="t")
        if tid is not None:
            return tid
        p_dict = parse_payload(row.get("payload"))
        return normalize_id(p_dict.get("track_id"), prefix="t")

    df["user_id"] = df["user_id"].apply(lambda v: normalize_id(v, prefix="u"))
    df["track_id"] = df.apply(resolve_track_id, axis=1)

    # Descartar usuarios anónimos o eventos sin canción asociada
    df = df[df["user_id"].notna() & df["track_id"].notna()].copy()
    df["w"] = df["event_type"].map(W)
    return df


def save(df, entity):
    """
    Guarda el DataFrame en Parquet local con particionado entity=/ingest_date=/part-0000.parquet
    y lo sube a S3 si S3_BUCKET está activo, conservando siempre la copia local si S3 falla.
    """
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rel = f"analytics/entity={entity}/ingest_date={d}/part-0000.parquet"
    path = f"datalake/{rel}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)

    s3_msg = ""
    if s3 and BUCKET:
        try:
            s3.upload_file(path, BUCKET, rel)
            s3_msg = f" y s3://{BUCKET}/{rel}"
        except Exception as exc:
            s3_msg = f" (ADVERTENCIA: falló subida a S3: {exc}; se conserva copia local)"
    print(f"Guardado {entity}: {len(df)} filas -> {path}{s3_msg}", flush=True)


def matrix(scores, all_tracks):
    M = scores.pivot_table(
        index="user_id",
        columns="track_id",
        values="w",
        aggfunc="sum",
        fill_value=0,
    )
    return M.reindex(columns=all_tracks, fill_value=0).clip(lower=0)


def item_sim(M):
    sim = cosine_similarity(M.T.values)
    np.fill_diagonal(sim, 0)
    return sim


def masked(S, M):
    S = S.astype(float).copy()
    S[M.values > 0] = -np.inf  # no recomendar lo que el usuario ya escuchó
    return S


def hit_rate(S, M, test, k=K):
    if test.empty or M.empty:
        return 0.0
    k_eff = min(k, M.shape[1])
    idx = np.argsort(-masked(S, M), axis=1)[:, :k_eff]
    cols = M.columns.values
    pos = {u: i for i, u in enumerate(M.index)}
    hits = [
        t in cols[idx[pos[u]]]
        for u, t in zip(test.user_id, test.track_id)
        if u in pos
    ]
    return float(np.mean(hits)) if hits else 0.0


def main():
    # ---------- 1. Datos ----------
    raw_df = load()
    df = clean_events(raw_df)

    if df.empty:
        print(
            "AVISO: Tras limpiar los datos no quedaron eventos válidos con user_id y track_id.\n"
            "Verifica que los CSV contengan eventos de reproducción/interacción de usuarios autenticados.",
            flush=True,
        )
        sys.exit(0)

    n_events = len(df)
    n_users = df["user_id"].nunique()
    n_tracks = df["track_id"].nunique()
    print(f"Eventos usados: {n_events} | usuarios: {n_users} | canciones: {n_tracks}", flush=True)

    if n_users < 20 or n_tracks < 20:
        print(
            f"ADVERTENCIA: Conjunto de datos pequeño ({n_users} usuarios, {n_tracks} canciones; "
            "recomendado >= 20). El modelo se entrenará igualmente.",
            flush=True,
        )

    scores = df.groupby(["user_id", "track_id"], as_index=False)["w"].sum()
    all_tracks = sorted(scores["track_id"].unique())
    k_eff = min(K, len(all_tracks))

    # ---------- 2. Evaluación: se oculta 1 canción positiva por usuario ----------
    pos_rows = scores[scores["w"] > 0]
    pos_counts = pos_rows.groupby("user_id")["track_id"].transform("count")
    eval_candidates = pos_rows[pos_counts >= 2]
    if eval_candidates.empty:
        eval_candidates = pos_rows

    if not eval_candidates.empty and len(all_tracks) > 1:
        test = eval_candidates.groupby("user_id").sample(1, random_state=1)
        train = scores.drop(test.index)
        if train.empty:
            train = scores.copy()
        Mt = matrix(train, all_tracks)
        hr_model = hit_rate(Mt.values @ item_sim(Mt), Mt, test, k=k_eff)
        pop = np.tile(Mt.values.sum(0), (len(Mt), 1))
        hr_pop = hit_rate(pop, Mt, test, k=k_eff)
    else:
        hr_model = 0.0
        hr_pop = 0.0

    hr_random = min(1.0, k_eff / max(1, len(all_tracks)))
    print(f"\nHit-rate@{k_eff} modelo item-item : {hr_model:.3f}", flush=True)
    print(f"Hit-rate@{k_eff} baseline popular : {hr_pop:.3f}", flush=True)
    print(f"Aleatorio (referencia)        : {hr_random:.3f}\n", flush=True)

    # ---------- 3. Modelo final con todos los datos ----------
    M = matrix(scores, all_tracks)
    S = masked(M.values @ item_sim(M), M)
    idx = np.argsort(-S, axis=1)[:, :k_eff]
    now = datetime.now(timezone.utc).isoformat()

    recs_rows = []
    for i, u in enumerate(M.index):
        for r, j in enumerate(idx[i]):
            score_val = float(S[i, j])
            if np.isneginf(score_val):
                continue
            recs_rows.append(
                {
                    "user_id": u,
                    "rank": r + 1,
                    "track_id": M.columns[j],
                    "score": round(score_val, 4),
                    "generated_at": now,
                }
            )
    recs = pd.DataFrame(
        recs_rows,
        columns=["user_id", "rank", "track_id", "score", "generated_at"],
    )
    save(recs, "recommendations")

    # ---------- 4. Perfil de usuario ----------
    prof = df.pivot_table(
        index="user_id",
        columns="event_type",
        values="event_id",
        aggfunc="count",
        fill_value=0,
    )
    prof = prof.reindex(columns=list(W), fill_value=0).reset_index()
    prof["skip_rate"] = (prof["skip"] / prof["play_start"].clip(lower=1)).round(4)
    save(prof, "user_profile")

    # ---------- 5. Métricas del modelo ----------
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    metrics_df = pd.DataFrame(
        [
            {
                "fecha": today_str,
                "hit_rate_modelo": round(float(hr_model), 4),
                "hit_rate_popular": round(float(hr_pop), 4),
                "azar": round(float(hr_random), 4),
                "n_usuarios": int(n_users),
                "n_canciones": int(n_tracks),
                "n_eventos": int(n_events),
            }
        ]
    )
    save(metrics_df, "model_metrics")

    if not recs.empty:
        sample_user = recs["user_id"].iloc[0]
        print(f"\nTop-{k_eff} recomendaciones para usuario '{sample_user}':", flush=True)
        print(recs[recs["user_id"] == sample_user].head(k_eff).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()

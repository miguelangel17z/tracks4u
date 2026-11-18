import glob
import io
import os

import pandas as pd

BUCKET = os.getenv("S3_BUCKET", "").strip() or None
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
ENTITIES = ["recommendations", "user_profile", "model_metrics"]


def read_entity_parquet(entity, s3_client=None):
    """Lee todos los Parquet de una entidad en analytics/ desde S3 o desde datalake/ local."""
    prefix = f"analytics/entity={entity}/"
    dfs = []

    if BUCKET and s3_client is not None:
        try:
            paginator = s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith(".parquet"):
                        body = s3_client.get_object(Bucket=BUCKET, Key=key)["Body"].read()
                        dfs.append(pd.read_parquet(io.BytesIO(body)))
            if dfs:
                return pd.concat(dfs, ignore_index=True), f"s3://{BUCKET}/{prefix}"
        except Exception as exc:
            print(
                f"ADVERTENCIA: No se pudo leer {prefix} desde S3 ({exc}); leyendo copia local...",
                flush=True,
            )

    local_files = sorted(glob.glob(f"datalake/analytics/entity={entity}/*/*.parquet"))
    for fpath in local_files:
        dfs.append(pd.read_parquet(fpath))
    if dfs:
        return pd.concat(dfs, ignore_index=True), f"datalake/{prefix}"
    return pd.DataFrame(), None


def main():
    s3_client = None
    if BUCKET:
        import boto3

        s3_client = boto3.client("s3", region_name=REGION)

    print("=" * 72, flush=True)
    print("VERIFICACIÓN DE SALIDAS EN ZONA ANALYTICS (PARQUET)", flush=True)
    print("=" * 72, flush=True)

    loaded = {}
    for entity in ENTITIES:
        df, source = read_entity_parquet(entity, s3_client)
        loaded[entity] = df
        if df.empty:
            print(f"- entity={entity:<18} : SIN DATOS", flush=True)
        else:
            print(f"- entity={entity:<18} : {len(df):>6} filas | origen: {source}", flush=True)

    metrics_df = loaded.get("model_metrics", pd.DataFrame())
    if not metrics_df.empty:
        print("\n--- Métricas de Evaluación (entity=model_metrics) ---", flush=True)
        print(metrics_df.tail(5).to_string(index=False), flush=True)

    recs_df = loaded.get("recommendations", pd.DataFrame())
    if not recs_df.empty:
        sample_user = recs_df["user_id"].iloc[0]
        print(f"\n--- Top 5 Recomendaciones para '{sample_user}' (entity=recommendations) ---", flush=True)
        user_recs = recs_df[recs_df["user_id"] == sample_user].sort_values("rank").head(5)
        print(user_recs.to_string(index=False), flush=True)

        prof_df = loaded.get("user_profile", pd.DataFrame())
        if not prof_df.empty and "user_id" in prof_df.columns:
            user_prof = prof_df[prof_df["user_id"] == sample_user]
            if not user_prof.empty:
                print(
                    f"\n--- Perfil de Comportamiento de '{sample_user}' (entity=user_profile) ---",
                    flush=True,
                )
                print(user_prof.to_string(index=False), flush=True)

    print("=" * 72, flush=True)


if __name__ == "__main__":
    main()

"""Phase 2G read-only Iceberg REST + MinIO integrity audit.

Never changes table data, snapshots, buckets or checkpoints.
Executes against the development REST fixture; passing does NOT establish
catalog durability, recovery, or production readiness.
"""
import argparse
import json
import os

from pyspark.sql import SparkSession, functions as F


def evaluate_metrics(metrics, expected_unique=None):
    """Pure validation for deterministic automated checks."""
    failures = []
    if metrics["silver_rows"] == 0:
        failures.append("Silver table is empty")
    if metrics["duplicate_event_ids"] != 0:
        failures.append("Silver contains duplicate event IDs")
    if metrics["null_silver_keys"] != 0:
        failures.append("Silver contains null key fields")
    if metrics["gold_mismatched_rows"] != 0:
        failures.append("Gold aggregates do not match Silver")
    for table, count in metrics["snapshot_counts"].items():
        if count < 1:
            failures.append(f"{table} has no Iceberg snapshots")
    if expected_unique is not None and metrics["silver_rows"] != expected_unique:
        failures.append(f"Expected {expected_unique} Silver rows, got {metrics['silver_rows']}")
    return failures


def run(expected_unique=None):
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        raise ValueError("S3 credentials are required from phase2f.env")
    spark = (
        SparkSession.builder.appName("DataNexus-Phase2G-ReadOnly-Audit")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.sql.catalog.remote", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.remote.type", "rest")
        .config("spark.sql.catalog.remote.uri", "http://iceberg-rest:8181")
        .config("spark.sql.catalog.remote.warehouse", "s3://warehouse/")
        .config("spark.sql.catalog.remote.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
        .config("spark.sql.catalog.remote.s3.endpoint", "http://minio:9000")
        .config("spark.sql.catalog.remote.s3.path-style-access", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    tables = {
        "silver": "remote.datanexus.silver_aviation",
        "quarantine": "remote.datanexus.quarantined_aviation",
        "gold": "remote.datanexus.gold_daily_aircraft",
    }
    try:
        silver = spark.table(tables["silver"])
        quarantine = spark.table(tables["quarantine"])
        gold = spark.table(tables["gold"])
        duplicates = silver.groupBy("event_id").count().filter(F.col("count") > 1).count()
        null_keys = silver.filter(
            F.col("event_id").isNull()
            | F.col("tenant_id").isNull()
            | F.col("icao24").isNull()
            | F.col("event_date").isNull()
        ).count()
        expected_gold = (
            silver.groupBy("tenant_id", "event_date")
            .agg(
                F.count("*").alias("event_count"),
                F.countDistinct("icao24").alias("distinct_aircraft"),
            )
        )
        gold_columns = ["tenant_id", "event_date", "event_count", "distinct_aircraft"]
        observed = gold.select(*gold_columns)
        expected = expected_gold.select(*gold_columns)
        mismatched = observed.exceptAll(expected).count() + expected.exceptAll(observed).count()

        snapshot_counts = {
            name: spark.table(f"{qualified}.snapshots").count()
            for name, qualified in tables.items()
        }
        metrics = {
            "silver_rows": silver.count(),
            "quarantine_rows": quarantine.count(),
            "gold_rows": gold.count(),
            "duplicate_event_ids": duplicates,
            "null_silver_keys": null_keys,
            "gold_mismatched_rows": mismatched,
            "snapshot_counts": snapshot_counts,
            "catalog": "rest_fixture_development_only",
            "audit_mode": "read_only",
        }
        failures = evaluate_metrics(metrics, expected_unique)
        metrics["passed"] = not failures
        metrics["failures"] = failures
        print("DATANEXUS_ICEBERG_AUDIT=" + json.dumps(metrics, sort_keys=True))
        if failures:
            raise SystemExit("Iceberg integrity audit failed: " + "; ".join(failures))
        return metrics
    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-unique", type=int, default=2)
    args = parser.parse_args()
    run(args.expected_unique)


if __name__ == "__main__":
    main()

"""Phase 2F experimental Iceberg REST catalog + MinIO S3 object storage.

Requires the earlier Phase 2D Bronze Parquet. Bounded full-snapshot refresh.
REST fixture catalog is for development only; its durability/HA is not
guaranteed. Individual table commits are atomic, but NOT cross-table atomic.
"""
import argparse
import json
import os

from pyspark.sql import SparkSession
from spark_iceberg_medallion import transform


def run(bronze_path, expected_unique=None):
    access = os.environ["AWS_ACCESS_KEY_ID"]
    secret = os.environ["AWS_SECRET_ACCESS_KEY"]
    if not access or not secret:
        raise ValueError("S3 credentials must not be empty")
    spark = (
        SparkSession.builder.appName("DataNexus-Phase2F-Iceberg-S3")
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
    try:
        spark.sql("CREATE NAMESPACE IF NOT EXISTS remote.datanexus")
        bronze = spark.read.parquet(bronze_path)
        silver, quarantine, gold = transform(bronze)
        bronze_count = bronze.count()
        silver_count = silver.count()
        bad_count = quarantine.count()
        gold_count = gold.count()
        if expected_unique is not None and silver_count != expected_unique:
            raise ValueError(f"Expected {expected_unique} distinct event IDs, got {silver_count}")
        if silver_count == 0:
            raise ValueError("Refusing to replace Iceberg tables with empty Silver dataset")
        # Independent Iceberg transactions; no atomicity across all three tables.
        silver.writeTo("remote.datanexus.silver_aviation").using("iceberg").createOrReplace()
        quarantine.writeTo("remote.datanexus.quarantined_aviation").using("iceberg").createOrReplace()
        gold.writeTo("remote.datanexus.gold_daily_aircraft").using("iceberg").createOrReplace()

        # Read back via REST catalog, not local Parquet paths.
        observed_silver = spark.table("remote.datanexus.silver_aviation").count()
        observed_gold = spark.table("remote.datanexus.gold_daily_aircraft").count()
        if observed_silver != silver_count or observed_gold != gold_count:
            raise AssertionError("Iceberg REST read-back count mismatch")

        summary = {
            "bronze_records": bronze_count,
            "silver_unique_records": observed_silver,
            "quarantined_records": bad_count,
            "gold_rows": observed_gold,
            "storage_format": "iceberg_rest_minio_s3",
            "catalog": "rest_fixture_development_only",
        }
        print("DATANEXUS_S3_ICEBERG_METRICS=" + json.dumps(summary, sort_keys=True))
        return summary
    finally:
        spark.stop()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bronze", default="/opt/project/data/streaming/bronze_parquet")
    p.add_argument("--expected-unique", type=int, default=2)
    a = p.parse_args()
    run(a.bronze, a.expected_unique)


if __name__ == "__main__":
    main()

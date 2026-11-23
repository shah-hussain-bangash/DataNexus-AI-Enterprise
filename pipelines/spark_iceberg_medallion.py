"""Phase 2E initial Iceberg milestone: Spark Bronze Parquet to Iceberg tables.

Bounded snapshot refresh, not continuously streamed, remote object storage,
or a multi-table atomic transaction. Re-runs rederive Silver and Gold from
all local Bronze data. Each Iceberg table is replaced atomically by Iceberg.
"""
import argparse
import json

from pyspark.sql import SparkSession, Window, functions as F


def transform(bronze):
    """Derive quality-controlled unique event rows and daily aggregates."""
    required = {"event_id", "tenant_id", "icao24", "raw_json", "kafka_offset",
                "kafka_partition", "topic", "quality_reason"}
    missing = required - set(bronze.columns)
    if missing:
        raise ValueError(f"Missing Bronze columns: {sorted(missing)}")
    parsed = bronze.withColumn(
        "reason",
        F.when(F.col("raw_json").isNull(), F.lit("missing_raw_json"))
         .when(F.col("quality_reason").isNotNull(), F.col("quality_reason"))
         .when(F.col("event_id").isNull() | (F.length(F.trim("event_id")) == 0),
               F.lit("missing_event_id"))
         .when(F.col("tenant_id").isNull() | (F.length(F.trim("tenant_id")) == 0),
               F.lit("missing_tenant_id"))
         .when(F.col("icao24").isNull() | (F.length(F.trim("icao24")) == 0),
               F.lit("missing_icao24"))
    )
    bad = parsed.filter(F.col("reason").isNotNull()).select(
        "topic", "kafka_partition", "kafka_offset", "event_id", "reason", "raw_json"
    )
    valid = parsed.filter(F.col("reason").isNull())
    window = Window.partitionBy("event_id").orderBy(
        F.col("kafka_offset").asc(), F.col("kafka_partition").asc()
    )
    silver = (
        valid.withColumn("row_number", F.row_number().over(window))
        .filter(F.col("row_number") == 1)
        .select("event_id", "tenant_id", "icao24",
                F.get_json_object("raw_json", "$.source_event_time").alias("source_event_time"),
                F.to_date(F.get_json_object("raw_json", "$.source_event_time")).alias("event_date"),
                F.get_json_object("raw_json", "$.source").alias("source"),
                "topic", "kafka_partition", "kafka_offset", "raw_json")
    )
    silver = silver.filter(F.col("event_date").isNotNull())
    gold = silver.groupBy("tenant_id", "event_date").agg(
        F.count("*").alias("event_count"),
        F.countDistinct("icao24").alias("distinct_aircraft"),
    )
    return silver, bad, gold


def run(bronze_path, warehouse_uri, expected_unique=None):
    spark = (
        SparkSession.builder.appName("DataNexus-Phase2E-Iceberg")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", warehouse_uri)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    try:
        spark.sql("CREATE NAMESPACE IF NOT EXISTS local.datanexus")
        bronze = spark.read.parquet(bronze_path)
        silver, quarantine, gold = transform(bronze)
        raw_count = bronze.count()
        silver_count = silver.count()
        quarantine_count = quarantine.count()
        gold_count = gold.count()
        if expected_unique is not None and silver_count != expected_unique:
            raise ValueError(f"Expected {expected_unique} unique events, found {silver_count}")
        if silver_count == 0:
            raise ValueError("No valid aircraft events; refusing to replace Iceberg tables")
        # Each table has Iceberg snapshot commits; replacement is NOT atomic across tables.
        silver.writeTo("local.datanexus.silver_aviation").using("iceberg").createOrReplace()
        quarantine.writeTo("local.datanexus.quarantined_aviation").using("iceberg").createOrReplace()
        gold.writeTo("local.datanexus.gold_daily_aircraft").using("iceberg").createOrReplace()
        result = {
            "bronze_records": raw_count,
            "silver_unique_records": silver_count,
            "quarantined_records": quarantine_count,
            "gold_rows": gold_count,
            "warehouse": warehouse_uri,
            "storage_format": "iceberg_hadoop_catalog_local",
        }
        print("DATANEXUS_ICEBERG_METRICS=" + json.dumps(result, sort_keys=True))
        print("DATANEXUS_ICEBERG_GOLD_ROWS=" + json.dumps([
            row.asDict(recursive=True) for row in
            spark.table("local.datanexus.gold_daily_aircraft").orderBy("tenant_id", "event_date").collect()
        ], sort_keys=True, default=str))
        return result
    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bronze", default="/opt/project/data/streaming/bronze_parquet")
    parser.add_argument("--warehouse", default="file:/opt/project/data/iceberg/warehouse")
    parser.add_argument("--expected-unique", type=int, default=2)
    args = parser.parse_args()
    run(args.bronze, args.warehouse, args.expected_unique)


if __name__ == "__main__":
    main()

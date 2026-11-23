"""Phase 2C Spark batch milestone.

Reads Phase 2B Silver JSONL, applies a Spark DataFrame quality gate, writes
Silver and daily Gold Parquet datasets. This is a bounded batch run, not yet
Kafka Structured Streaming or an Iceberg transactional lakehouse.
"""
import argparse
import json

from pyspark.sql import SparkSession, functions as F, types as T

SCHEMA = T.StructType([
    T.StructField("event_id", T.StringType()),
    T.StructField("tenant_id", T.StringType()),
    T.StructField("icao24", T.StringType()),
    T.StructField("event_time", T.StringType()),
    T.StructField("event_date", T.StringType()),
    T.StructField("latitude", T.DoubleType()),
    T.StructField("longitude", T.DoubleType()),
    T.StructField("on_ground", T.BooleanType()),
    T.StructField("velocity_mps", T.DoubleType()),
    T.StructField("source", T.StringType()),
])


def run(input_path, output_path, expected_events=None):
    spark = (SparkSession.builder.appName("DataNexus-Phase2C-Medallion")
             .config("spark.sql.shuffle.partitions", "2")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    try:
        raw = spark.read.schema(SCHEMA).json(input_path)
        valid = (
            F.col("event_id").isNotNull()
            & F.col("tenant_id").isNotNull()
            & F.col("icao24").isNotNull()
            & F.col("event_date").rlike(r"^\d{4}-\d{2}-\d{2}$")
            & F.col("latitude").between(-90.0, 90.0)
            & F.col("longitude").between(-180.0, 180.0)
        )
        # A materialized cache avoids repeated parsing while counting and writing.
        dedup = raw.dropDuplicates(["event_id"]).cache()
        silver = dedup.filter(valid).cache()
        rejected = dedup.filter(~valid).cache()
        count = silver.count()
        bad_count = rejected.count()
        if expected_events is not None and count != expected_events:
            raise ValueError(f"Expected {expected_events} valid records, found {count}")
        gold = (
            silver.groupBy("tenant_id", "event_date")
            .agg(
                F.count("*").alias("event_count"),
                F.countDistinct("icao24").alias("distinct_aircraft"),
            )
        )
        gold_count = gold.count()
        # Snapshot overwrite: not atomic across paths or transactional.
        silver.write.mode("overwrite").parquet(output_path + "/silver_parquet")
        rejected.write.mode("overwrite").parquet(output_path + "/quarantine_parquet")
        gold.write.mode("overwrite").parquet(output_path + "/gold_parquet")
        metrics = {
            "silver_records": count,
            "quarantined_records": bad_count,
            "gold_rows": gold_count,
            "storage_format": "parquet_spark_batch",
        }
        print("DATANEXUS_SPARK_METRICS=" + json.dumps(metrics, sort_keys=True))
        return metrics
    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to Phase 2B Silver JSONL")
    parser.add_argument("--output", required=True, help="Spark Parquet output root")
    parser.add_argument("--expected-events", type=int)
    args = parser.parse_args()
    run(args.input, args.output, args.expected_events)


if __name__ == "__main__":
    main()

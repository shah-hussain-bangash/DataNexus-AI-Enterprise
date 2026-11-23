"""Phase 2D checkpointed Kafka -> Spark Structured Streaming -> Bronze Parquet.

This bounded streaming run uses availableNow: it processes available offsets and
exits. Restart the command to process later records using the same checkpoint.
It is NOT a continuous production service, curated Silver/Gold stream, or Iceberg.
"""
import argparse
import json

from pyspark.sql import SparkSession, functions as F, types as T


EVENT_SCHEMA = T.StructType([
    T.StructField("event_id", T.StringType()),
    T.StructField("schema_version", T.StringType()),
    T.StructField("tenant_id", T.StringType()),
    T.StructField("source", T.StringType()),
    T.StructField("source_event_time", T.StringType()),
    T.StructField("payload", T.StructType([
        T.StructField("icao24", T.StringType()),
        T.StructField("latitude", T.DoubleType()),
        T.StructField("longitude", T.DoubleType()),
    ])),
])


def validate_args(args):
    if not args.bootstrap.strip() or not args.topic.strip():
        raise ValueError("Kafka bootstrap and topic must not be empty")
    if not args.output.strip() or not args.checkpoint.strip():
        raise ValueError("Output and checkpoint locations must not be empty")
    if args.output.rstrip("/") == args.checkpoint.rstrip("/"):
        raise ValueError("Output and checkpoint paths must be separate")
    if not args.output.startswith("/") or not args.checkpoint.startswith("/"):
        raise ValueError("Use absolute container paths for Spark output and checkpoint")


def run(args):
    validate_args(args)
    spark = (SparkSession.builder
             .appName("DataNexus-Phase2D-Kafka-Bronze")
             .config("spark.sql.shuffle.partitions", "2")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    try:
        source = (
            spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", args.bootstrap)
            .option("subscribe", args.topic)
            .option("startingOffsets", "earliest")
            .option("failOnDataLoss", "true")
            .load()
        )
        records = (
            source.select(
                F.col("topic"),
                F.col("partition").alias("kafka_partition"),
                F.col("offset").alias("kafka_offset"),
                F.col("timestamp").alias("kafka_timestamp"),
                F.col("key").cast("string").alias("kafka_key"),
                F.col("value").cast("string").alias("raw_json"),
            )
            .withColumn("event", F.from_json("raw_json", EVENT_SCHEMA))
            .withColumn("event_id", F.col("event.event_id"))
            .withColumn("tenant_id", F.col("event.tenant_id"))
            .withColumn("icao24", F.col("event.payload.icao24"))
            .withColumn(
                "quality_reason",
                F.when(F.col("event").isNull(), F.lit("malformed_json"))
                 .when(F.col("event_id").isNull(), F.lit("missing_event_id"))
                 .when(F.col("tenant_id").isNull(), F.lit("missing_tenant_id"))
                 .when(F.col("icao24").isNull(), F.lit("missing_icao24"))
                 .when(~F.col("event.payload.latitude").between(-90.0, 90.0),
                       F.lit("missing_or_invalid_latitude"))
                 .when(~F.col("event.payload.longitude").between(-180.0, 180.0),
                       F.lit("missing_or_invalid_longitude"))
            )
            .drop("event")
        )
        query = (
            records.writeStream
            .format("parquet")
            .outputMode("append")
            .option("path", args.output)
            .option("checkpointLocation", args.checkpoint)
            .trigger(availableNow=True)
            .start()
        )
        query.awaitTermination()
        if query.exception() is not None:
            raise RuntimeError(str(query.exception()))
        print("DATANEXUS_STREAM_COMPLETED=" + json.dumps({
            "topic": args.topic,
            "output": args.output,
            "checkpoint": args.checkpoint,
            "last_progress": query.lastProgress,
        }, sort_keys=True, default=str))
    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", default="redpanda:9092")
    parser.add_argument("--topic", default="aviation.states.v1")
    parser.add_argument("--output", default="/opt/project/data/streaming/bronze_parquet")
    parser.add_argument("--checkpoint", default="/opt/project/data/streaming/checkpoints/aviation_bronze_v1")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()

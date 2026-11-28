"""Exercise Bronze validation and Iceberg medallion transforms with local Spark."""
from importlib.util import find_spec
import json
import unittest


@unittest.skipUnless(find_spec("pyspark"), "requires PySpark")
class SparkAviationQualityTests(unittest.TestCase):
    def test_invalid_records_are_quarantined_and_valid_replay_is_deduplicated(self):
        from pyspark.sql import SparkSession, functions as F

        from pipelines.spark_iceberg_medallion import transform
        from pipelines.spark_kafka_stream import prepare_bronze

        spark = (
            SparkSession.builder.master("local[2]")
            .appName("DataNexus aviation quality regression")
            .config("spark.ui.enabled", "false")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.ansi.enabled", "true")
            .getOrCreate()
        )
        self.addCleanup(spark.stop)
        spark.sparkContext.setLogLevel("WARN")

        def event(event_id, *, stamp="2026-01-01T00:15:00Z", latitude=25.2, longitude=55.3):
            return json.dumps({
                "event_id": event_id,
                "tenant_id": "demo",
                "source": "opensky.states.all",
                "source_event_time": stamp,
                "payload": {"icao24": "aaaaaa", "latitude": latitude, "longitude": longitude},
            })

        records = [
            event("first"),
            event("first"),
            event("bad-time", stamp="invalid"),
            event("no-latitude", latitude=None),
            "{invalid",
            None,
            event("bad-longitude", longitude=181.0),
            event("no-time", stamp=None),
        ]
        source = spark.createDataFrame(
            [("aviation.states.v1", 0, i, "aaaaaa", raw) for i, raw in enumerate(records)],
            "topic string, partition int, offset long, key string, value string",
        ).withColumn("timestamp", F.current_timestamp())
        bronze = prepare_bronze(source)
        reasons = {row.kafka_offset: row.quality_reason for row in bronze.collect()}
        self.assertEqual(reasons[3], "missing_or_invalid_latitude")
        self.assertEqual(reasons[4], "malformed_json")
        self.assertEqual(reasons[5], "missing_raw_json")
        self.assertEqual(reasons[6], "missing_or_invalid_longitude")

        # Older Bronze output could store missing coordinates without a reason.
        bronze = bronze.withColumn(
            "quality_reason",
            F.when(F.col("kafka_offset") != 3, F.col("quality_reason")),
        )
        silver, quarantine, gold = transform(bronze)
        self.assertEqual([(row.event_id, row.kafka_offset) for row in silver.collect()], [("first", 0)])
        self.assertEqual({row.kafka_offset: row.reason for row in quarantine.collect()}, {
            2: "missing_or_invalid_event_time",
            3: "missing_or_invalid_latitude",
            4: "malformed_json",
            5: "missing_raw_json",
            6: "missing_or_invalid_longitude",
            7: "missing_or_invalid_event_time",
        })
        self.assertEqual([(row.event_count, row.distinct_aircraft) for row in gold.collect()], [(1, 1)])


if __name__ == "__main__":
    unittest.main()

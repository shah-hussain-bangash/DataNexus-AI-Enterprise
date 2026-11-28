"""Export a bounded fixture snapshot of the local aviation Gold table for Power BI."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from pyspark.sql import SparkSession


TABLE = "local.datanexus.gold_daily_aircraft"
FIXTURE_TENANT = "demo"
MAX_ROWS = 366


def export(spark, output):
    refs = spark.table(f"{TABLE}.refs").where("name = 'main'").select("snapshot_id").collect()
    if len(refs) != 1:
        raise ValueError("Expected exactly one main Iceberg snapshot")
    snapshot_id = refs[0].snapshot_id
    if type(snapshot_id) is not int or snapshot_id <= 0:
        raise ValueError("Invalid Iceberg snapshot ID")
    rows = (
        spark.read.format("iceberg").option("snapshot-id", str(snapshot_id)).load(TABLE)
        .where("tenant_id = 'demo'")
        .select("event_date", "event_count", "distinct_aircraft")
        .orderBy("event_date")
        .limit(MAX_ROWS + 1)
        .collect()
    )
    if not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError("Fixture reporting window is empty or exceeds the row limit")
    dates = set()
    records = []
    for row in rows:
        if row.event_date is None or row.event_date in dates:
            raise ValueError("Gold requires one non-null row per date")
        if not (
            type(row.event_count) is int
            and type(row.distinct_aircraft) is int
            and 1 <= row.distinct_aircraft <= row.event_count
        ):
            raise ValueError("Gold reporting counts do not reconcile")
        dates.add(row.event_date)
        records.append({
            "date": row.event_date.isoformat(),
            "events": row.event_count,
            "aircraft": row.distinct_aircraft,
        })
    payload = {
        "schema_version": 1,
        "source": TABLE,
        "snapshot_id": str(snapshot_id),
        "source_scope": "isolated fixture replay",
        "tenant": FIXTURE_TENANT,
        "exported_utc": datetime.now(timezone.utc).isoformat(),
        "rows": records,
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=".gold-", suffix=".json",
            dir=output.parent, delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, output)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    print("DATANEXUS_GOLD_POWER_BI_EXPORT=" + json.dumps({
        "source": TABLE, "snapshot_id": str(snapshot_id), "rows": len(records),
    }, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warehouse", default="file:/opt/project/data/iceberg/warehouse")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    spark = (
        SparkSession.builder.appName("DataNexus G2 Power BI Gold export")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.local.type", "hadoop")
        .config("spark.sql.catalog.local.warehouse", args.warehouse)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    try:
        export(spark, args.output)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

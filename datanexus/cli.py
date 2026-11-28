"""Phase 2 CLI: fixture/live collector, Kafka producer and idempotent consumer."""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from datanexus.events import normalize_states
from datanexus.opensky import OpenSkyClient, OpenSkyRateLimited
from datanexus.storage import LocalEventStore

LOG = logging.getLogger("datanexus")
FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "opensky-states.json"


def broker():
    try:
        from confluent_kafka import Producer, Consumer
        return Producer, Consumer
    except ImportError as exc:
        raise SystemExit("Install Kafka dependency: pip install -e '.[kafka]'") from exc


def produce(events, address, topic):
    Producer, _ = broker()
    producer = Producer({"bootstrap.servers": address, "enable.idempotence": True,
                         "acks": "all", "message.timeout.ms": 15000})
    errors = []
    for event in events:
        producer.produce(topic, key=event["payload"]["icao24"],
                         value=json.dumps(event), on_delivery=lambda error, msg: errors.append(str(error)) if error else None)
        producer.poll(0)
    pending = producer.flush(30)
    if pending or errors:
        raise RuntimeError(f"Failed deliveries: pending={pending}; errors={errors[:3]}")
    LOG.info("Published %d events to %s", len(events), topic)


def fixture_events(path):
    with open(path, encoding="utf-8") as stream:
        return normalize_states(json.load(stream), collected_at="2026-01-01T00:00:00Z")


def collect_live_once(args, client, bbox):
    """Make one authenticated poll and publish only a fresh, nonempty result."""
    if not client.client_id.strip() or not client.client_secret.strip():
        raise SystemExit("Set OPENSKY_CLIENT_ID and OPENSKY_CLIENT_SECRET before a live one-shot run.")
    try:
        response = client.states(bbox)
        provider_time = response.get("time") if isinstance(response, dict) else None
        if type(provider_time) is not int:
            raise SystemExit("OpenSky returned an invalid snapshot timestamp.")
        age_seconds = time.time() - provider_time
        if not -30 <= age_seconds <= 120:
            raise SystemExit("OpenSky snapshot time is outside the live acceptance window.")
        events = normalize_states(response)
    except OpenSkyRateLimited as exc:
        raise SystemExit(f"OpenSky rate limited the request. Retry after {exc.retry_seconds} seconds.") from None
    except HTTPError as exc:
        raise SystemExit(f"OpenSky returned HTTP {exc.code}. Nothing was published.") from None
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        raise SystemExit(f"OpenSky one-shot collection failed ({type(exc).__name__}). Nothing was published.") from None

    if not events:
        raise SystemExit("OpenSky returned no valid aircraft events for this area.")
    produce(events, args.bootstrap, args.topic)
    LOG.info("Live snapshot published: provider_unix_time=%d, events=%d", provider_time, len(events))


def collect(args):
    if args.mode == "fixture":
        events = fixture_events(args.fixture)
        produce(events, args.bootstrap, args.topic)
        return
    if not args.once and args.interval < 60:
        raise SystemExit("Live collection interval must be >=60 seconds to protect API credits")
    bbox = (args.lamin, args.lomin, args.lamax, args.lomax)
    client = OpenSkyClient()
    if args.once:
        collect_live_once(args, client, bbox)
        return
    while True:
        try:
            events = normalize_states(client.states(bbox))
            produce(events, args.bootstrap, args.topic)
            time.sleep(args.interval)
        except OpenSkyRateLimited as exc:
            LOG.warning("Rate limited; sleeping %s seconds", exc.retry_seconds)
            time.sleep(max(args.interval, exc.retry_seconds))
        except (OSError, ValueError, RuntimeError) as exc:
            LOG.exception("Collection failed; retrying: %s", exc)
            time.sleep(max(args.interval, 120))


def consume(args):
    _, Consumer = broker()
    store = LocalEventStore(args.db)
    consumer = Consumer({
        "bootstrap.servers": args.bootstrap, "group.id": "datanexus-aviation-v1",
        "auto.offset.reset": "earliest", "enable.auto.commit": False,
    })
    consumer.subscribe([args.topic])
    LOG.info("Consuming %s into %s", args.topic, args.db)
    try:
        while True:
            message = consumer.poll(1)
            if message is None:
                continue
            if message.error():
                raise RuntimeError(str(message.error()))
            try:
                event = json.loads(message.value())
                inserted = store.put(event)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                # Intentionally stop: poison messages need an audited DLQ policy, not silent loss.
                LOG.error("Invalid event at offset %s: %s", message.offset(), exc)
                raise
            consumer.commit(message=message, asynchronous=False)
            if inserted:
                LOG.info("Stored event %s", event["event_id"][:12])
    finally:
        consumer.close()
        store.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("collect")
    p.add_argument("--mode", choices=["fixture", "live"], default=os.getenv("SOURCE_MODE", "fixture"))
    p.add_argument("--fixture", default=str(FIXTURE))
    p.add_argument("--once", action="store_true", help="In live mode, poll once and exit.")
    p.add_argument("--bootstrap", default=os.getenv("KAFKA_BOOTSTRAP", "localhost:19092"))
    p.add_argument("--topic", default=os.getenv("KAFKA_TOPIC", "aviation.states.v1"))
    p.add_argument("--interval", type=int, default=int(os.getenv("POLL_INTERVAL_SECONDS", "120")))
    p.add_argument("--lamin", type=float, default=float(os.getenv("OPENSKY_LAMIN", "24.8")))
    p.add_argument("--lamax", type=float, default=float(os.getenv("OPENSKY_LAMAX", "25.3")))
    p.add_argument("--lomin", type=float, default=float(os.getenv("OPENSKY_LOMIN", "54.9")))
    p.add_argument("--lomax", type=float, default=float(os.getenv("OPENSKY_LOMAX", "55.6")))
    q = sub.add_parser("consume")
    q.add_argument("--bootstrap", default=os.getenv("KAFKA_BOOTSTRAP", "localhost:19092"))
    q.add_argument("--topic", default=os.getenv("KAFKA_TOPIC", "aviation.states.v1"))
    q.add_argument("--db", default=os.getenv("SQLITE_PATH", "data/dev/aviation.sqlite3"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        if args.command == "collect":
            collect(args)
        else:
            consume(args)
    except KeyboardInterrupt:
        LOG.info("Stopped by operator")


if __name__ == "__main__":
    main()

"""Durable local approval records for read-only MTA investigation briefs."""

from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from uuid import uuid4


ACTION = "accept_mta_investigation_brief"
TTL_SECONDS = 3600
SCHEMA = """
CREATE TABLE IF NOT EXISTS review_requests (
    id TEXT PRIMARY KEY, tenant TEXT NOT NULL, submitter TEXT NOT NULL,
    assessment TEXT NOT NULL, evidence_json TEXT NOT NULL, evidence_sha256 TEXT NOT NULL,
    created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS review_decisions (
    request_id TEXT PRIMARY KEY REFERENCES review_requests(id),
    reviewer TEXT NOT NULL, decision TEXT NOT NULL CHECK(decision IN ('approve','reject')),
    decided_at INTEGER NOT NULL
);
"""


class ReviewConflict(ValueError):
    pass


class SelfReview(PermissionError):
    pass


def evidence(brief):
    text = json.dumps({"action": ACTION, "brief": brief}, sort_keys=True, separators=(",", ":"))
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def db_path(data_root):
    return Path(data_root).resolve() / "mta" / "human_review.sqlite3"


def connect(path, *, readonly=False):
    connection = sqlite3.connect(path.as_uri() + "?mode=ro" if readonly else path, uri=readonly, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def request_row(connection, tenant, request_id):
    return connection.execute(
        """SELECT r.*, d.reviewer, d.decision, d.decided_at FROM review_requests r
           LEFT JOIN review_decisions d ON d.request_id = r.id
           WHERE r.id = ? AND r.tenant = ?""",
        (request_id, tenant),
    ).fetchone()


def present(row, now):
    if row is None:
        return None
    encoded = row["evidence_json"]
    if hashlib.sha256(encoded.encode("utf-8")).hexdigest() != row["evidence_sha256"]:
        raise ValueError("Stored review evidence fails its integrity check")
    record = json.loads(encoded)
    if record["action"] != ACTION or record["brief"]["assessment"]["snapshot_sha256"] != row["assessment"]:
        raise ValueError("Stored review scope does not match its evidence")
    status = {"approve": "approved", "reject": "rejected"}.get(row["decision"])
    return {
        "request_id": row["id"],
        "assessment_sha256": row["assessment"],
        "action": ACTION,
        "evidence_sha256": row["evidence_sha256"],
        "evidence": record["brief"],
        "submitted_by": row["submitter"],
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
        "status": status or ("expired" if now >= row["expires_at"] else "pending"),
        "decision": {"by": row["reviewer"], "at": row["decided_at"], "choice": row["decision"]} if status else None,
    }


def submit(data_root, tenant, actor, brief, *, now=None):
    instant = int(time.time() if now is None else now)
    path = db_path(data_root)
    text, digest = evidence(brief)
    assessment = brief["assessment"]["snapshot_sha256"]
    request_id = uuid4().hex
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as connection:
        connection.executescript(SCHEMA)
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute(
                """SELECT id FROM review_requests WHERE tenant=? AND submitter=?
                   AND evidence_sha256=? AND expires_at>? ORDER BY created_at DESC LIMIT 1""",
                (tenant, actor, digest, instant),
            ).fetchone()
            if prior is not None:
                request_id = prior["id"]
            else:
                connection.execute(
                    """INSERT INTO review_requests
                       (id,tenant,submitter,assessment,evidence_json,evidence_sha256,created_at,expires_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (request_id, tenant, actor, assessment, text, digest, instant, instant + TTL_SECONDS),
                )
            return present(request_row(connection, tenant, request_id), instant)


def get(data_root, tenant, request_id, *, now=None):
    path = db_path(data_root)
    if not path.is_file():
        return None
    instant = int(time.time() if now is None else now)
    with closing(connect(path, readonly=True)) as connection:
        return present(request_row(connection, tenant, request_id), instant)


def decide(data_root, tenant, actor, request_id, decision, expected_digest, current_brief, *, now=None):
    path = db_path(data_root)
    if not path.is_file():
        return None
    instant = int(time.time() if now is None else now)
    with closing(connect(path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        brief = present(request_row(connection, tenant, request_id), instant)
        if brief is None:
            return None
        if brief["submitted_by"].casefold() == actor.casefold():
            raise SelfReview("A submitter cannot decide their own request")
        if brief["evidence_sha256"] != expected_digest:
            raise ReviewConflict("Expected evidence digest does not match")
        prior = brief["decision"]
        if prior is not None:
            if prior["by"] == actor and prior["choice"] == decision:
                return brief
            raise ReviewConflict("The request already has a decision")
        if brief["status"] != "pending":
            raise ReviewConflict("Review request has expired")
        if current_brief is None or evidence(current_brief)[1] != expected_digest:
            raise ReviewConflict("Investigation evidence changed after submission")
        connection.execute(
            "INSERT INTO review_decisions (request_id, reviewer, decision, decided_at) VALUES (?,?,?,?)",
            (request_id, actor, decision, instant),
        )
        return present(request_row(connection, tenant, request_id), instant)

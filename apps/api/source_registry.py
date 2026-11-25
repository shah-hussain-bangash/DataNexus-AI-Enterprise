"""Grounded source contracts and a fail-closed readiness manifest.

This module deliberately does NOT claim that an external dataset, collector,
stream, Power BI report or enterprise release control is active.
Provider URLs here are documentation identifiers, not fetched credentials.
"""
from copy import deepcopy

SOURCE_CONTRACTS = (
    {"id":"mobility","name":"Urban Mobility","region":"New York City","historical":"NYC TLC trip records and MTA hourly station ridership","latest":"MTA GTFS-Realtime trip updates and alerts","update_model":"realtime_proposed"},
    {"id":"weather","name":"Weather & Climate","region":"United States","historical":"NOAA GHCN-hourly archives","latest":"NWS station observations and alerts","update_model":"provider_dependent"},
    {"id":"seismic","name":"Seismic Activity","region":"Global","historical":"USGS ComCat catalog","latest":"USGS recent earthquakes GeoJSON","update_model":"realtime_proposed"},
    {"id":"coastal","name":"Coastal Water Levels","region":"United States","historical":"NOAA CO-OPS verified historical records","latest":"NOAA CO-OPS preliminary water-level data","update_model":"provider_dependent"},
    {"id":"river","name":"River & Watershed","region":"United States","historical":"USGS historical streamflow","latest":"USGS latest continuous streamflow","update_model":"provider_dependent"},
    {"id":"property","name":"Dubai Property","region":"Dubai, UAE","historical":"Dubai Land Department sales / rental data (licensing pending)","latest":"Scheduled published batch (not a real-time stream)","update_model":"scheduled"},
    {"id":"energy","name":"Energy Grid","region":"United States","historical":"EIA-930 archive","latest":"EIA latest available hourly balancing data","update_model":"hourly_latest"},
)

RELEASE_CONTROLS = (
    "identity_sso_mfa","authorization_tenant_isolation","data_ingestion_resilience",
    "stream_processing_recovery","lakehouse_integrity","api_security_and_rate_limits",
    "ml_model_evaluation","genai_grounding_and_safety","agent_approval_audit",
    "observability_and_alerting","secrets_supply_chain","disaster_recovery",
    "load_and_performance","deployment_rollbacks","data_licensing_and_privacy",
    "end_to_end_acceptance",
)

def catalog(tenant_id):
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise ValueError("Verified tenant is required")
    return {
        "tenant_id":tenant_id,
        "environment":"local-development",
        "source_kind":"design_contract",
        "sources":[{
            **deepcopy(source),
            "historical_state":"not_connected",
            "latest_state":"not_connected",
            "verified_rows":None,
            "provider_observed_at":None,
            "last_successful_fetch_at":None,
            "approved_snapshot":None,
            "license_review":"pending",
        } for source in SOURCE_CONTRACTS],
        "caveat":"Contracts are intended sources, NOT evidence of completed ingestion.",
    }

def readiness(tenant_id):
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise ValueError("Verified tenant is required")
    return {
        "tenant_id":tenant_id,
        "environment":"local-development",
        "release_status":"blocked",
        "approved_controls":0,
        "required_controls":len(RELEASE_CONTROLS),
        "controls":[{"id":name,"status":"no_approved_evidence"} for name in RELEASE_CONTROLS],
        "domains_connected":0,
        "next_step":"Independent evidence-based review; do not infer readiness from unit tests or a frontend build.",
    }

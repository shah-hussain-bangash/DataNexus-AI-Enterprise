export type Capability={id:number;name:string};
export type CapabilityGroup={name:string;items:Capability[]};
export const capabilityGroups:CapabilityGroup[]=[
  {
    "name": "Dashboard UI/UX",
    "items": [
      {
        "id": 1,
        "name": "Cross-domain selector/navigation"
      },
      {
        "id": 2,
        "name": "NYC historical analytics screen"
      },
      {
        "id": 3,
        "name": "NYC live operations screen"
      },
      {
        "id": 4,
        "name": "Station detail screen"
      },
      {
        "id": 5,
        "name": "Data health screen"
      },
      {
        "id": 6,
        "name": "Date/dataset/region/station/route filters"
      },
      {
        "id": 7,
        "name": "URL-backed filters and deep links"
      },
      {
        "id": 8,
        "name": "Verified geographic maps"
      },
      {
        "id": 9,
        "name": "Paginated accessible data tables"
      },
      {
        "id": 10,
        "name": "Authorized tenant-scoped exports"
      },
      {
        "id": 11,
        "name": "Complete loading/empty/stale/unavailable/unauthorized states"
      },
      {
        "id": 12,
        "name": "Mobile/keyboard/accessibility browser acceptance"
      }
    ]
  },
  {
    "name": "Domain integrations",
    "items": [
      {
        "id": 13,
        "name": "NYC TLC + MTA domain adapter"
      },
      {
        "id": 14,
        "name": "NOAA/NWS weather adapter"
      },
      {
        "id": 15,
        "name": "USGS seismic adapter"
      },
      {
        "id": 16,
        "name": "NOAA coastal adapter"
      },
      {
        "id": 17,
        "name": "USGS river adapter"
      },
      {
        "id": 18,
        "name": "Licensed Dubai property source adapter"
      },
      {
        "id": 19,
        "name": "EIA energy adapter"
      },
      {
        "id": 20,
        "name": "Governed source/domain catalog and policy signoff"
      }
    ]
  },
  {
    "name": "Historical big data",
    "items": [
      {
        "id": 21,
        "name": "NYC TLC historical acquisition"
      },
      {
        "id": 22,
        "name": "MTA station ridership historical acquisition"
      },
      {
        "id": 23,
        "name": "Immutable source manifest and checksums"
      },
      {
        "id": 24,
        "name": "Bronze immutable raw storage"
      },
      {
        "id": 25,
        "name": "Spark schema and business validation"
      },
      {
        "id": 26,
        "name": "Quarantine invalid records"
      },
      {
        "id": 27,
        "name": "Silver and Gold Iceberg tables"
      },
      {
        "id": 28,
        "name": "Verified station-zone geographic crosswalk"
      },
      {
        "id": 29,
        "name": "Atomic PostgreSQL reporting publication"
      },
      {
        "id": 30,
        "name": "1/3/12 month benchmarks"
      }
    ]
  },
  {
    "name": "Streaming data",
    "items": [
      {
        "id": 31,
        "name": "MTA trip-update collector"
      },
      {
        "id": 32,
        "name": "MTA service-alert collector"
      },
      {
        "id": 33,
        "name": "Versioned Kafka topics and event envelopes"
      },
      {
        "id": 34,
        "name": "Spark streaming checkpoint and watermark"
      },
      {
        "id": 35,
        "name": "Deduplication/reordering with verified tests"
      },
      {
        "id": 36,
        "name": "PostgreSQL station/alert projections"
      },
      {
        "id": 37,
        "name": "Snapshot and SSE delivery"
      },
      {
        "id": 38,
        "name": "Reconnect and polling fallback"
      },
      {
        "id": 39,
        "name": "Last-good data and stale/unavailable states"
      },
      {
        "id": 40,
        "name": "Collector/processor restart and recovery E2E tests"
      }
    ]
  },
  {
    "name": "Power BI",
    "items": [
      {
        "id": 41,
        "name": "Executive Overview published report"
      },
      {
        "id": 42,
        "name": "Mobility Explorer published report"
      },
      {
        "id": 43,
        "name": "Station Detail published report"
      },
      {
        "id": 44,
        "name": "Feed Health published report"
      },
      {
        "id": 45,
        "name": "Authenticated governed semantic model"
      },
      {
        "id": 46,
        "name": "Dimensions and reconciled DAX measures"
      },
      {
        "id": 47,
        "name": "Refresh scheduling, validation and parity checks"
      },
      {
        "id": 48,
        "name": "Row-level security and authorized exports"
      }
    ]
  },
  {
    "name": "ML/GenAI/Agents",
    "items": [
      {
        "id": 49,
        "name": "Chronological forecasting baseline"
      },
      {
        "id": 50,
        "name": "Evaluation, monitoring and drift controls"
      },
      {
        "id": 51,
        "name": "Model and feature version registry"
      },
      {
        "id": 52,
        "name": "Read-only grounded GenAI metrics assistant"
      },
      {
        "id": 53,
        "name": "Evidence citations and safe abstention"
      },
      {
        "id": 54,
        "name": "Read-only incident investigation agent"
      },
      {
        "id": 55,
        "name": "Human approval, action audit and supervision"
      }
    ]
  },
  {
    "name": "Security/governance",
    "items": [
      {
        "id": 56,
        "name": "Enterprise OIDC integration"
      },
      {
        "id": 57,
        "name": "MFA enforcement"
      },
      {
        "id": 58,
        "name": "Multi-user fine-grained RBAC"
      },
      {
        "id": 59,
        "name": "Session revocation and expiry testing"
      },
      {
        "id": 60,
        "name": "Two-tenant isolation/security validation"
      },
      {
        "id": 61,
        "name": "TLS, network policies and workload identities"
      },
      {
        "id": 62,
        "name": "Secret rotation and encryption"
      },
      {
        "id": 63,
        "name": "Distributed API rate limits and secured data exports"
      },
      {
        "id": 64,
        "name": "Lineage, retention, privacy and licensed source ownership"
      }
    ]
  },
  {
    "name": "Production/reliability",
    "items": [
      {
        "id": 65,
        "name": "Integrated observability and metrics"
      },
      {
        "id": 66,
        "name": "Incident alerts and ownership"
      },
      {
        "id": 67,
        "name": "Backups and restore drills"
      },
      {
        "id": 68,
        "name": "Load and performance benchmarks"
      },
      {
        "id": 69,
        "name": "Separate staging and production environments"
      },
      {
        "id": 70,
        "name": "CI/CD supply-chain, artifact signing and scanning"
      },
      {
        "id": 71,
        "name": "Canary deployments, rollback and disaster recovery"
      },
      {
        "id": 72,
        "name": "16-control independent release evidence signoff"
      }
    ]
  }
];

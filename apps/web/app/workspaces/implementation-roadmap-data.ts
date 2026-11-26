/* Implementation and verification roadmap, separate from the 72-group acceptance register. */
export type RoadmapTask = {id:number;title:string};
export type RoadmapGroup = {name:string;items:RoadmapTask[]};
export const implementationRoadmap:RoadmapGroup[] = [
  {
    "name": "UI/UX and Dashboard",
    "items": [
      {
        "id": 1,
        "title": "Final desktop and mobile testing"
      },
      {
        "id": 2,
        "title": "Accessibility and keyboard navigation verification"
      },
      {
        "id": 3,
        "title": "Real-data dashboard charts and maps"
      },
      {
        "id": 4,
        "title": "Complete interactive filtering and drill-down"
      },
      {
        "id": 5,
        "title": "Paginated data tables"
      },
      {
        "id": 6,
        "title": "Secure data exports"
      },
      {
        "id": 7,
        "title": "Complete loading, error and unavailable states"
      }
    ]
  },
  {
    "name": "Real Data Integrations",
    "items": [
      {
        "id": 8,
        "title": "NYC TLC and MTA integration"
      },
      {
        "id": 9,
        "title": "NOAA/NWS weather integration"
      },
      {
        "id": 10,
        "title": "USGS earthquake integration"
      },
      {
        "id": 11,
        "title": "NOAA coastal data integration"
      },
      {
        "id": 12,
        "title": "USGS river data integration"
      },
      {
        "id": 13,
        "title": "Dubai Land Department data integration"
      },
      {
        "id": 14,
        "title": "EIA energy data integration"
      },
      {
        "id": 15,
        "title": "Source licensing and governance approval"
      }
    ]
  },
  {
    "name": "Historical Big Data",
    "items": [
      {
        "id": 16,
        "title": "Complete historical data ingestion"
      },
      {
        "id": 17,
        "title": "Data validation and quality checks"
      },
      {
        "id": 18,
        "title": "Immutable Bronze storage"
      },
      {
        "id": 19,
        "title": "Silver and Gold Iceberg tables"
      },
      {
        "id": 20,
        "title": "Invalid-record quarantine"
      },
      {
        "id": 21,
        "title": "PostgreSQL analytics integration"
      },
      {
        "id": 22,
        "title": "Historical benchmarking and forecasting datasets"
      }
    ]
  },
  {
    "name": "Live Streaming",
    "items": [
      {
        "id": 23,
        "title": "Real-time API collectors"
      },
      {
        "id": 24,
        "title": "Production Kafka pipelines"
      },
      {
        "id": 25,
        "title": "Spark Structured Streaming"
      },
      {
        "id": 26,
        "title": "Stream deduplication and recovery"
      },
      {
        "id": 27,
        "title": "Real-time dashboard updates"
      },
      {
        "id": 28,
        "title": "Automatic reconnection and fallback"
      },
      {
        "id": 29,
        "title": "Streaming monitoring and alerting"
      }
    ]
  },
  {
    "name": "Power BI",
    "items": [
      {
        "id": 30,
        "title": "Published Power BI reports"
      },
      {
        "id": 31,
        "title": "Production semantic models"
      },
      {
        "id": 32,
        "title": "Validated DAX measures"
      },
      {
        "id": 33,
        "title": "Scheduled dataset refresh"
      },
      {
        "id": 34,
        "title": "Row-level security"
      },
      {
        "id": 35,
        "title": "Secure Power BI embedding"
      },
      {
        "id": 36,
        "title": "Governed report exports"
      }
    ]
  },
  {
    "name": "Machine Learning",
    "items": [
      {
        "id": 37,
        "title": "Production forecasting models"
      },
      {
        "id": 38,
        "title": "Anomaly detection models"
      },
      {
        "id": 39,
        "title": "Model evaluation and monitoring"
      },
      {
        "id": 40,
        "title": "Model drift detection"
      },
      {
        "id": 41,
        "title": "Feature engineering pipelines"
      },
      {
        "id": 42,
        "title": "Model registry and versioning"
      },
      {
        "id": 43,
        "title": "MLOps deployment pipelines"
      }
    ]
  },
  {
    "name": "Generative AI",
    "items": [
      {
        "id": 44,
        "title": "Real LLM integration"
      },
      {
        "id": 45,
        "title": "Retrieval-Augmented Generation (RAG)"
      },
      {
        "id": 46,
        "title": "Vector database integration"
      },
      {
        "id": 47,
        "title": "Grounded AI responses with citations"
      },
      {
        "id": 48,
        "title": "AI evaluation and hallucination controls"
      },
      {
        "id": 49,
        "title": "Secure enterprise knowledge retrieval"
      }
    ]
  },
  {
    "name": "Agentic AI",
    "items": [
      {
        "id": 50,
        "title": "Functional AI investigation agents"
      },
      {
        "id": 51,
        "title": "Tool and API integration"
      },
      {
        "id": 52,
        "title": "Multi-step agent orchestration"
      },
      {
        "id": 53,
        "title": "Human-in-the-loop approvals"
      },
      {
        "id": 54,
        "title": "Agent activity auditing"
      },
      {
        "id": 55,
        "title": "Agent monitoring and safety controls"
      }
    ]
  },
  {
    "name": "Enterprise Security and Governance",
    "items": [
      {
        "id": 56,
        "title": "Enterprise SSO/OIDC"
      },
      {
        "id": 57,
        "title": "Multi-factor authentication"
      },
      {
        "id": 58,
        "title": "Fine-grained RBAC"
      },
      {
        "id": 59,
        "title": "Tenant isolation verification"
      },
      {
        "id": 60,
        "title": "TLS and workload identities"
      },
      {
        "id": 61,
        "title": "Secret rotation and encryption"
      },
      {
        "id": 62,
        "title": "API rate limiting"
      },
      {
        "id": 63,
        "title": "Data lineage and privacy enforcement"
      },
      {
        "id": 64,
        "title": "Security penetration testing"
      }
    ]
  },
  {
    "name": "Production Engineering",
    "items": [
      {
        "id": 65,
        "title": "Production cloud deployment"
      },
      {
        "id": 66,
        "title": "Separate development, staging and production environments"
      },
      {
        "id": 67,
        "title": "CI/CD deployment automation"
      },
      {
        "id": 68,
        "title": "Infrastructure monitoring and observability"
      },
      {
        "id": 69,
        "title": "Incident management"
      },
      {
        "id": 70,
        "title": "Automated backups and recovery"
      },
      {
        "id": 71,
        "title": "Load and performance testing"
      },
      {
        "id": 72,
        "title": "Canary deployments and rollback"
      },
      {
        "id": 73,
        "title": "Disaster recovery testing"
      },
      {
        "id": 74,
        "title": "High availability and scalability"
      },
      {
        "id": 75,
        "title": "Independent end-to-end acceptance testing"
      },
      {
        "id": 76,
        "title": "Approval of all 16 production release controls"
      }
    ]
  }
];

# Identity Enrichment Service

Identity enrichment service that synchronizes selected identity
attributes from Active Directory into a local identity data store
and exposes them through a FastAPI API.

## Architecture

                 ON-PREM
┌──────────────────────────────────┐
│                                  │
│  Active Directory                │
│        │                         │
│        │ LDAPS                   │
│        ▼                         │
│  Identity Enrichment             │
│  Middleware                      │
│        │                         │
│        ▼                         │
│  Local Identity Store            │
│  (only required attributes)      │
│                                  │
└──────────────────────────────────┘
                 │
                 │ HTTPS API
                 ▼
        Cloud Security Platform

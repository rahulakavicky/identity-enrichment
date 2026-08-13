# Identity Enrichment Service

Identity enrichment service that synchronizes selected identity
attributes from Active Directory into a local identity data store
and exposes them through a FastAPI API.

## Architecture

Active Directory
        |
        | LDAPS
        v
Identity Syncer
        |
        v
Identity Database
        |
        v
FastAPI
        |
        v
Security/XDR Platform

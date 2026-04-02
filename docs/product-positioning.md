# Product Positioning

## Chosen Wedge

Primary wedge: `citation attestation for agents`

Rejected for now:

- broad `truth layer` positioning
- general-purpose fact-checking
- multi-tool MCP expansion
- crypto-first branding that leads with payments instead of utility

## Messaging Gap

| Area | What users may assume | What the product actually guarantees today |
| --- | --- | --- |
| `Truth` branding | The service can verify whether a claim is true | The service fetches a URL and reports what it observed |
| Anti-hallucination message | The service prevents citation mistakes end to end | The service only checks the fetched source and optional substring presence |
| Verification | The source is trustworthy and unchanged | The source resolved at a specific time and produced the returned metadata/hash |
| Claim support | Claim matching is semantic | Claim matching is substring-only |
| Payments | Payments are the product | Payments are the access control and anti-abuse rail |

## Current Guarantee

The service can currently attest that:

- a URL was fetched at a specific time
- the request resolved or redirected
- the final URL and status code observed
- the response body hash that was observed
- whether a literal claim string appeared in the fetched body

## Non-Goals For This Iteration

- semantic fact-checking
- trust scoring for sources
- content provenance beyond the fetched response
- marketplace/growth optimization before user validation

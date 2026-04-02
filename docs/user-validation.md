# User Validation Runbook

## Objective

Validate whether `citation attestation for agents` is compelling enough that teams would use it instead of a plain fetch plus internal logging.

## Target Profiles

Interview exactly 5 people before adding major features:

1. Agent platform builder shipping MCP-compatible tools
2. Research-agent developer who cites external URLs in outputs
3. AI workflow owner with audit or compliance requirements
4. Tooling engineer responsible for rate limiting or abuse controls
5. Founder or PM deciding whether citation reliability is worth paying for

## The One Question

`Would you use this instead of a normal fetch plus logs? Why or why not?`

## Follow-Up Questions

1. What is the failure mode you care about most: dead links, redirects, changed content, or unsupported claims?
2. Is a `content_sha256` hash useful in your workflow?
3. Would you pay for this as a standalone API, or only if it plugged into an existing agent framework?
4. At what point would this become indispensable instead of nice-to-have?
5. What proof would you need beyond status code and redirects?

## Pass / Fail Criteria

Pass if at least 3 of 5 interviewees say one of the following:

- they would use it in a real workflow
- they already have this problem and current tooling is inadequate
- the attestation metadata is meaningfully better than a plain fetch

Fail if the dominant reaction is one of:

- `nice demo, not needed`
- `we already do this with fetch plus logs`
- `the payment flow adds more friction than value`

## Interview Log Template

| Interviewee | Role | Pain point | Would use it? | Objection | Needed proof |
| --- | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |
| 4 |  |  |  |  |  |
| 5 |  |  |  |  |  |

## What To Do After The 5 Interviews

- If the pass criteria are met, deepen attestation with stronger content evidence.
- If users want abuse control more than attestation, pivot messaging toward economic gating.
- If the fail criteria dominate, stop adding product surface area and rewrite the wedge.

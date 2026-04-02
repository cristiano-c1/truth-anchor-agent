# User Validation Proxy

This is a proxy validation memo based on 5 public market signals. It is not a substitute for direct interviews, but it is enough to guide positioning before adding more product surface area.

## Signal 1: Dead-link handling is a real agent failure mode

Source: [Agent 404: Tool to Prevent AI Agents from Hitting Dead Links and Hallucinating](https://agent-wars.com/news/2026-03-15-agent-404-dead-links-ai-agents)

Takeaway:

- Broken or stale URLs are already being framed as an agent-specific product problem.
- Availability checks are useful, but they are only one layer of the problem.

## Signal 2: Citation verification is emerging as a separate category

Source: [CiteAudit](https://hyper.ai/en/papers/2602.23452)

Takeaway:

- The market is moving toward explicit citation verification systems rather than generic anti-hallucination messaging.
- Stronger products in this space combine retrieval, metadata checks, and deterministic validation.

## Signal 3: Legal and enterprise users care about verification, not branding

Source: [AI Citation Hallucinations in Legal Research: The Verification Problem Nobody Has Solved Yet](https://www.lextrapolate.com/news/ai-citation-hallucinations-legal-research-verification-problem)

Takeaway:

- High-risk users care about evidence chains and verification workflows.
- `Truth` language is less compelling than `what was checked, when, and against what source`.

## Signal 4: Builders are already shipping citation-auditing tools

Source: [ai-citation-auditor](https://github.com/leonjvr/ai-citation-auditor)

Takeaway:

- Developers are treating citation auditing as its own workflow with tool access and structured checks.
- This supports a wedge around `citation attestation for agents`.

## Signal 5: x402 is strongest as a payment/control rail

Source: [x402: How AI Agents Pay for API Calls with HTTP](https://dev.to/walletguy/x402-how-ai-agents-pay-for-api-calls-with-http-3hna)

Takeaway:

- The strongest public story around x402 is machine-to-machine access control and paid API usage.
- Payments should support the attestation wedge, not define the product on their own.

## Verdict

The current best wedge is still `citation attestation for agents`.

Why:

- public signals confirm that source reliability and citation checking are real problems
- adjacent products are positioning around verification and auditability
- the payment rail is a supporting advantage, not the main reason users care

## Next Step

Use `docs/user-validation.md` to run 5 direct interviews with target users. If those interviews do not show strong pull, pivot the product story toward economic gating instead of expanding attestation features.

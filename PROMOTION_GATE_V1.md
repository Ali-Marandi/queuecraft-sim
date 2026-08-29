# QueueCraft Promotion Gate v1

Before a challenger is eligible for Champion review, QueueCraft evaluates a deterministic governance gate.

## Required checks

- Accepted validation status: `validated` or `validated_with_limits`
- Data quality score at least `0.80`
- No unresolved input drift state marked `drift`
- Challenger improves the primary metric by the configured minimum
- Evidence fingerprint is present

The gate returns `eligible: true/false` and a list of blocking reasons. It never promotes or deploys a model.

## Governance boundary

The gate is advisory control logic. Final promotion remains a human approval action recorded by the model registry. Deployment is deliberately outside this component.

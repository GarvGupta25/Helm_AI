#!/usr/bin/env bash
set -euo pipefail
# Generated exact inverse MOVE commands. NOT EXECUTED during this task.
cd -- "$(git rev-parse --show-toplevel)"
if [ "$(git branch --show-current)" = main ]; then printf "%s\n" "Create a restoration branch first; refusing to change main." >&2; exit 1; fi
git diff --quiet
git diff --cached --quiet
check_move() {
  if [ ! -f "$1" ] || [ -e "$2" ]; then printf "%s\n" "Restore preflight failed: $1 -> $2 (missing source or occupied destination)" >&2; exit 1; fi
}
# Preflight every move before making any changes.
check_move archive/broker-workspace/frontend/src/Broker.tsx frontend/src/Broker.tsx
check_move archive/broker-workspace/frontend/src/MarketplaceBrokerPanel.tsx frontend/src/MarketplaceBrokerPanel.tsx
check_move archive/broker-workspace/tests/e2e/broker-marketplace.spec.ts tests/e2e/broker-marketplace.spec.ts
check_move archive/provider-workspace/frontend/src/provider/ProviderApplications.tsx frontend/src/provider/ProviderApplications.tsx
check_move archive/provider-workspace/frontend/src/provider/ProviderFinancialAccounts.tsx frontend/src/provider/ProviderFinancialAccounts.tsx
check_move archive/provider-workspace/frontend/src/provider/ProviderFlagForm.tsx frontend/src/provider/ProviderFlagForm.tsx
check_move archive/provider-workspace/frontend/src/provider/ProviderPolicies.tsx frontend/src/provider/ProviderPolicies.tsx
check_move archive/provider-workspace/frontend/src/provider/ProviderQuoteForm.tsx frontend/src/provider/ProviderQuoteForm.tsx
check_move archive/provider-workspace/frontend/src/provider/ProviderWorkspace.tsx frontend/src/provider/ProviderWorkspace.tsx
check_move archive/provider-workspace/frontend/src/provider/types.ts frontend/src/provider/types.ts
check_move archive/provider-workspace/tests/e2e/provider-workspace.spec.ts tests/e2e/provider-workspace.spec.ts
check_move archive/claim-review/frontend/src/broker/ClaimReview.tsx frontend/src/broker/ClaimReview.tsx
check_move archive/claim-review/frontend/src/broker/ClaimOperations.tsx frontend/src/broker/ClaimOperations.tsx
check_move archive/claim-review/tests/e2e/claim-review.spec.ts tests/e2e/claim-review.spec.ts
check_move archive/_unused/frontend/src/components/CalculationStepper.tsx frontend/src/components/CalculationStepper.tsx
check_move archive/_unused/frontend/src/marketing/hooks/useScrollReveal.ts frontend/src/marketing/hooks/useScrollReveal.ts
check_move archive/_unused/frontend/public/assets/helm-assistant.json frontend/public/assets/helm-assistant.json
# The following commands reverse every actual move, preserving history.
mkdir -p -- frontend/src
git mv -- archive/broker-workspace/frontend/src/Broker.tsx frontend/src/Broker.tsx
mkdir -p -- frontend/src
git mv -- archive/broker-workspace/frontend/src/MarketplaceBrokerPanel.tsx frontend/src/MarketplaceBrokerPanel.tsx
mkdir -p -- tests/e2e
git mv -- archive/broker-workspace/tests/e2e/broker-marketplace.spec.ts tests/e2e/broker-marketplace.spec.ts
mkdir -p -- frontend/src/provider
git mv -- archive/provider-workspace/frontend/src/provider/ProviderApplications.tsx frontend/src/provider/ProviderApplications.tsx
mkdir -p -- frontend/src/provider
git mv -- archive/provider-workspace/frontend/src/provider/ProviderFinancialAccounts.tsx frontend/src/provider/ProviderFinancialAccounts.tsx
mkdir -p -- frontend/src/provider
git mv -- archive/provider-workspace/frontend/src/provider/ProviderFlagForm.tsx frontend/src/provider/ProviderFlagForm.tsx
mkdir -p -- frontend/src/provider
git mv -- archive/provider-workspace/frontend/src/provider/ProviderPolicies.tsx frontend/src/provider/ProviderPolicies.tsx
mkdir -p -- frontend/src/provider
git mv -- archive/provider-workspace/frontend/src/provider/ProviderQuoteForm.tsx frontend/src/provider/ProviderQuoteForm.tsx
mkdir -p -- frontend/src/provider
git mv -- archive/provider-workspace/frontend/src/provider/ProviderWorkspace.tsx frontend/src/provider/ProviderWorkspace.tsx
mkdir -p -- frontend/src/provider
git mv -- archive/provider-workspace/frontend/src/provider/types.ts frontend/src/provider/types.ts
mkdir -p -- tests/e2e
git mv -- archive/provider-workspace/tests/e2e/provider-workspace.spec.ts tests/e2e/provider-workspace.spec.ts
mkdir -p -- frontend/src/broker
git mv -- archive/claim-review/frontend/src/broker/ClaimReview.tsx frontend/src/broker/ClaimReview.tsx
mkdir -p -- frontend/src/broker
git mv -- archive/claim-review/frontend/src/broker/ClaimOperations.tsx frontend/src/broker/ClaimOperations.tsx
mkdir -p -- tests/e2e
git mv -- archive/claim-review/tests/e2e/claim-review.spec.ts tests/e2e/claim-review.spec.ts
mkdir -p -- frontend/src/components
git mv -- archive/_unused/frontend/src/components/CalculationStepper.tsx frontend/src/components/CalculationStepper.tsx
mkdir -p -- frontend/src/marketing/hooks
git mv -- archive/_unused/frontend/src/marketing/hooks/useScrollReveal.ts frontend/src/marketing/hooks/useScrollReveal.ts
mkdir -p -- frontend/public/assets
git mv -- archive/_unused/frontend/public/assets/helm-assistant.json frontend/public/assets/helm-assistant.json
printf "%s\n" "Moved files restored. Review original routing/styles/config snapshots as described in archive/README.md before rebuilding."

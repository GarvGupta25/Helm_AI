# Verification — 23 October 2026

The new implementation is a synthetic research/public-chat demo. This report does not change the original transformation's real-service NO-GO assessment.

| Check | Observed result |
|---|---|
| Full backend suite | 401 passed, 1 pre-existing skip; 187.27 seconds |
| Final research/public-chat targeted suite | 32 passed; includes generator quote counts, filters, simulation arithmetic, memory bounds, encryption/isolation, confirmation, mock extraction and uploads/SSE |
| Frontend unit tests | 10 passed across UI primitives and safe markdown/SSE tests |
| Frontend typecheck / scoped ESLint | Passed |
| Backend Ruff | Passed for app, tests, scripts and migrations |
| Backend lock consistency | `uv lock --project backend --check` passed |
| Demo build | Passed with `VITE_NEXT_CHAT_UI=true`; existing Home static/dynamic import and dependency annotation warnings remain non-fatal |
| Public/research browser suite | 15 passed; production preview and isolated real API |
| Preserved customer browser suite | 9 passed |
| New UI regression rerun | Six research/chat flows also rerun after final widget fixes |
| Axe on research/open chat/Arabic dark chat | No reported violations in checked scoped states |
| Research desktop Lighthouse | Performance 100, accessibility 100, best practices 96, SEO 91 |
| New chat bundle | About 49.94 KB gzip JS + 3.10 KB CSS, excluding the existing optional Lottie runtime |
| Generated fixture evaluation | 60 personas, zero hard-filter violations; 105 selected-item clause-reference checks passed |
| GitHub implementation CI | [Successful run for 816cbae](https://github.com/GarvGupta25/Helm_AI/actions/runs/39995711961) |

NDCG@3 and Hit@3 in `evaluation.json` are agreement with a **generated template clause/price oracle**, not independently reviewed preference relevance. The report states this limitation alongside the numbers. Latency measurements are local, synthetic and machine-dependent; no production SLA is claimed.

Evidence is in `docs/chatbot-screenshots`, `docs/uk/evidence/playwright.json`, `generator-quality.json`, `evaluation.json`, `dataset-sample.json` and `personas.json`. The full generated JSON/CSV files are under ignored `.runtime/synthetic-uk-v1` on the local machine and can be regenerated from source.

Reproduction commands:

```powershell
$env:VITE_NEXT_CHAT_UI='true'
npm --prefix frontend run build
npm --prefix frontend test
npm --prefix frontend run lint:uk
uv run --project backend ruff check backend/app backend/tests backend/scripts backend/migrations
uv run --project backend pytest backend/tests -q
npm run test:uk
npm run test:e2e
```

Real microphones/browser permission dialogs, physical mobile keyboards/camera, screen readers, independent Arabic wording review, live Groq calls, a deployed OCR environment and live PostgreSQL execution are **not verified**. Learned ranking stays disabled. No real customer database migration, callback/email delivery, hosting deployment, transaction or regulated-service sign-off occurred. The earlier original-plan mobile performance/migration/legal gaps remain documented separately.

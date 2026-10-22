# Verification record — 22/10/2026

These are actual local results for the implementation checkpoint, not launch certification.

| Check | Result |
|---|---|
| Production-mode demo bundle | PASS: `npm --prefix frontend run build` |
| Live release guard | EXPECTED BLOCK: `build:production` rejects unresolved identity and launch blockers |
| TypeScript | PASS: `npm --prefix frontend run check` |
| Frontend lint | PASS on `src/uk`, `src/ui`, `src/market` |
| Frontend primitive tests | 5 passed |
| Full backend suite | 369 passed, 1 skipped |
| Backend coverage | 94% combined; domain 95%, servicing 95%, UK quote 91%, UK router 86% |
| Migration and seed | SQLite up/down, idempotent seed: 30 plans and 23,100 rate rows |
| UK browser suite | 9 passed against the final built preview in 1.1 minutes |
| Preserved customer browser suite | 9 passed in 30.9 seconds, including sign-out and authoritative role checks |
| Automated WCAG rules | 0 critical/serious on Home, About, underwriting, initial quote screen and privacy |
| Responsive viewport captures | Home and About at 375/768/1280/1920; no horizontal overflow |
| Dependency audit | Root and frontend: 0 reported vulnerabilities at verification time |
| Python lockfile | `uv lock --project backend --check` passes |
| New UK public-source guard | PASS (scoped; not whole-repository certification) |
| Whole historical inventory | 359 tracked-source matches; not zero |
| Lighthouse desktop Home / About | Performance 99 / 100; accessibility 100 / 100; best practices 96 / 96; SEO 91 / 91 |
| Lighthouse mobile Home / About | Performance 83 / 79; About misses the 80 target; lab LCP 2.95s / 3.29s misses 2.5s |

The 14 required assistant inputs and 200 adversarial variations are included in the backend suite. Tests use reviewed knowledge mode; they do not evaluate a live Groq/LangGraph public conversation. No real customer database was migrated. No real payment was attempted. The sole skipped backend test remains skipped as in the original suite.

Browser evidence records automated checks only. Manual NVDA/VoiceOver, zoom/device matrix, real-user comprehension, legal/DPO approvals and full launch gates remain incomplete. Baseline contrast failures are retained in `axe-home-before.json`; current route reports contain empty violation arrays. Lighthouse scores are reported exactly in the measured report, including any missed targets.

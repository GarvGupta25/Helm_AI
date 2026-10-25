# Guided journey — final QA record

Date: 25 October 2026. Automated synthetic data only. Actual command results are in WIZARD_PROGRESS.md. This checklist is not WCAG, legal or production certification.

| Check | Execution / limit |
|---|---|
| Wizard, optional skip/edit/undo, mode switch, plan filters/detail/compare/selection | Automated desktop1440 and mobile375 browser suites |
| Verification, access, dashboard PDF/assistant, broker sharing/review | Real local API/worker; broker sign-in UI uses a fixture, separate API role/assignment tests |
| Axe serious/critical checks | Scoped automated pages; does not replace manual accessibility testing |
| Keyboard | Automated focus on step heading, Space for choice, Enter for Next; full keyboard-only manual journey pending |
| Narrow reflow | Automated320/375 CSS viewport; physical400% browser zoom and OS magnification pending |
| Dark, reduced motion and RTL structure | Automated emulation; English content retained per prior explicit request. Arabic wording review not applicable; no Arabic picker restored |
| Physical mobile touch/scroll and soft keyboard | Not executed: no attached iOS/Android device used |
| Manual screen reader | Not executed: NVDA/VoiceOver owner check required |
| Network offline, slow4G, flaky voice/microphone | API error/fallback code and automated tests; real device/network/manual pass pending |
| Live WhatsApp/SMTP/Groq and Supabase broker sign-in | Not exercised; no approved credentials/template/account supplied; local sandbox stays console |
| PostgreSQL race tests, edge rate limits and hosted headers | SQLite tests and local application limits only; deployed infrastructure review pending |

Before a real pilot: run iPhone Safari and Android Chrome portrait/landscape, keyboard open, safe-area and nested scrolling; navigate every control with Tab/Shift+Tab/Enter/Space/Escape; NVDA+Firefox and VoiceOver+Safari through errors/progress/dialogs; 200/400% zoom; evaluate on the supported browser/device matrix; collect genuine UK user feedback. Record device/browser/version, findings, fixes and reviewer/date rather than marking this list passed by assumption.

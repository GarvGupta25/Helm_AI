# Measured browser evidence

Local lab measurements, not production field data. Missing runs are not passes.

| Report | Performance | Accessibility | Best practices | SEO | LCP (ms) | CLS |
|---|---:|---:|---:|---:|---:|---:|
| lighthouse-about-desktop.json | 100 | 100 | 96 | 91 | 683 | 0.0 |
| lighthouse-about-mobile.json | 79 | 100 | 96 | 91 | 3291 | 0.016 |
| lighthouse-home-desktop-before.json | 44 | 96 | 96 | 91 | 2905 | 0.017 |
| lighthouse-home-desktop.json | 99 | 100 | 96 | 91 | 777 | 0.011 |
| lighthouse-home-mobile.json | 83 | 100 | 96 | 91 | 2954 | 0.016 |

## Accessibility runs

- axe--.json: 0 rule violations; 0 critical/serious rules.
- axe--about.json: 0 rule violations; 0 critical/serious rules.
- axe--get-cover-quote.json: 0 rule violations; 0 critical/serious rules.
- axe--get-cover-underwriting.json: 0 rule violations; 0 critical/serious rules.
- axe--legal-privacy.json: 0 rule violations; 0 critical/serious rules.
- axe-home-before.json: 1 rule violations; 1 critical/serious rules.

## Browser suite

Actual recorded stats: `{"startTime": "2026-10-22T16:17:55.582Z", "duration": 64138.288, "expected": 9, "skipped": 0, "unexpected": 0, "flaky": 0}`.

## Backend coverage

| Module | Line coverage |
|---|---:|
| backend\app\domain.py | 94.8% |
| backend\app\market\__init__.py | 100.0% |
| backend\app\market\models.py | 100.0% |
| backend\app\market\quote.py | 90.5% |
| backend\app\market\router.py | 86.2% |
| backend\app\market\seed.py | 100.0% |
| backend\app\market\uk.py | 100.0% |
| backend\app\public_assistant.py | 94.5% |
| backend\app\servicing.py | 94.8% |

# Captured tokens — 25 October 2026

Sources read: frontend/src/ui/uk.css, uk/site.css, journey/journey.css. Reuse these rather than install a UI library.

| Token / rule | Actual value |
|---|---|
| --uk-brand | #4b4dff |
| --uk-ink / --uk-muted | #172c32 / #52666a |
| --uk-teal / --uk-mint | #053b44 / #e4f6f3 |
| --uk-cream / --uk-line | #f6f3ee / #c9d4d3 |
| --uk-ease | cubic-bezier(.22,1,.36,1) |
| journey --j-navy / --j-teal / --j-line | #142c43 / #087c7a / #cfdae0 |
| Fonts | Inter 400/500/600 local WOFF2; Instrument Serif regular/italic for emphasis |
| Site body | 16px / 1.65 |
| H1 | clamp(2.8rem,5.7vw,6rem), weight400, tracking -.035em |
| Quote H2 | 1.65rem / 1.2 |
| Inputs | 16px, min-height48px, border #8194a2, radius12px, padding12px |
| Journey buttons | min-height44px, radius12px, padding10px 16px, navy primary |
| Site button | min-height50px, padding13px 25px, pill999px |
| Cards / panel | radius20px /18px; line border; white /#f4f7f9 |
| Action bar | sticky bottom12px, radius18px, shadow 0 6px 24px #142c4312 |
| Focus | journey 2px teal +3px offset; site3px #5759ff +4px offset |
| Motion | journey color160ms only when no reduced motion; global reduce disables animation/transition |
| Responsive | journey 900px collapse; site 900/520px; safe-area bottom on action bar |

Current quote has no translated Arabic or scoped dark rule. English removal was already delivered; do not restore it. Structural RTL variants use logical spacing and grid direction; new dark rules must be scoped and use the current navy/white palette, leaving header/footer untouched. Baseline screenshots show current light/dark-media behavior accurately, even when visually identical. No guessed design token is presented as captured.

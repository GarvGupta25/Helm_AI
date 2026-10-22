# Architecture decisions

- Preserve the existing customer authentication and professional archive split.
- The actual baseline uses React 19. It is retained; the brief's React 18 description was not used to justify a downgrade.
- Public UK pages render without waiting for an authenticated API configuration request.
- UK quote calculation is additive and server-owned. All new monetary values are integer pence with currency GBP; historical records are never reinterpreted by renaming units.
- Radix for modal, navigation and tooltip focus behaviour; native labelled form controls; React Router for routes; CSS for inexpensive motion; reduced-motion must disable all loops.
- Self-host open fonts. No third-party analytics or tracking before opt-in.
- New tables are additive, reversible and separate from historical policy records. Live database migrations are not automatically applied.
- Existing scoped agent architecture is retained. Claims outcomes remain deterministic and owned by servicing.py.
- GSAP/Lenis are deferred until measured choreography warrants the bundle cost. A static original illustration is preferable to an unlicensed photo.

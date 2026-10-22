# Superseded public-site browser tests

These tests target the previous public website's navigation, copy and catalogue contracts. They are preserved, not deleted. The rebuilt public site is tested by `tests/uk/public.spec.ts`; customer/auth/marketplace browser regressions remain active in `tests/e2e/`.

The new suite covers four widths, keyboard navigation, cookie choice, external links, reduced motion, automated WCAG rules, quote comparison/confirmation and chat handoff. Full manual zoom, screen-reader and device coverage remains an explicit launch gap; archiving old fixtures does not count as passing those checks.

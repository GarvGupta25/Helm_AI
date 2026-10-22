# _unused

## Purpose

Unreferenced compatibility re-export, scroll-reveal hook and old assistant animation asset.

## Preserved entry

No live entry route. Canonical customer CalculationStepper.tsx and robot.json remain in the main site.

Original files are listed in ../MANIFEST.md and are byte-preserved at move time. No backend files or environment files are copied here.

## Why these files were archived

- frontend/src/components/CalculationStepper.tsx is an unreferenced one-line re-export; Shopping imports frontend/src/CalculationStepper.tsx directly.
- frontend/src/marketing/hooks/useScrollReveal.ts has no inbound source/test/config references.
- frontend/public/assets/helm-assistant.json has no tracked references; the live public assistant loads robot.json.

## Dependencies and restoration

The hook needs React and the browser IntersectionObserver API. The re-export needs the canonical CalculationStepper.tsx from the main site if restored. The JSON is a Lottie asset. There are no API endpoints or environment variables. The unused files are not an application by themselves.

For reuse: 1. create a new repo; 2. copy only the desired original-path files from this folder; 3. add package.json/Vite config if building a React app; 4. set any application env vars (none required by these files); 5. point the surrounding application's API base URL at the existing backend only if needed; 6. add auth/role guards for any protected app around them. Use ../restore.sh only for exact original-path restoration after reviewing its preflight.

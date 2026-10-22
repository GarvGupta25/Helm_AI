import { readFileSync, readdirSync, statSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const live = process.argv.includes('--live') || process.env.HELM_RELEASE_MODE === 'live';
const paths = ['frontend/src/uk', 'frontend/src/market'];
const errors = [];
function scan(path) {
  if (statSync(path).isDirectory()) { for (const name of readdirSync(path)) scan(resolve(path, name)); return; }
  if (!/\.(tsx?|css)$/.test(path)) return;
  const source = readFileSync(path, 'utf8');
  if (/\b(?:UAE|AED|Dubai|DHA|DOH|HAAD|emirates?|razorpay|fils)\b|PD-05-2025|\+971/i.test(source)) errors.push(`Legacy-market term in UK public source: ${path}`);
}
paths.forEach(path => scan(resolve(root, path)));
if (live) {
  // Fail closed: identity alone cannot resolve product, operational and migration blockers.
  errors.push('Live release blocked: demo-only market configuration, unapproved IPIDs, incomplete historical migration and missing compliance/legal/DPO/user-research sign-off. See docs/uk/LAUNCH_READINESS.md.');
  const config = readFileSync(resolve(root, 'frontend/src/market/uk.config.ts'), 'utf8');
  if (/\[TBC\]|\[FIRM NAME\]|\[ADDRESS TBC\]/.test(config)) errors.push('Unresolved regulatory placeholders.');
}
if (errors.length) { errors.forEach(error => console.error(error)); process.exitCode = 1; }
else console.log('UK public-source guard passed. Demo build only; this is not a whole-repository clearance.');

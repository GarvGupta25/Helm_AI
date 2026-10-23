import js from '@eslint/js';
import tseslint from 'typescript-eslint';
export default tseslint.config({ ignores: ['dist/**', 'node_modules/**'] }, {
  files: ['src/uk/**/*.{ts,tsx}', 'src/ui/**/*.{ts,tsx}', 'src/market/**/*.ts', 'src/marketing/chat/**/*.{ts,tsx}'],
  extends: [js.configs.recommended, ...tseslint.configs.recommended],
});

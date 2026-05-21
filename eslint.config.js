// Root-level ESLint flat config for super-linter.
// When ESLint is invoked from the repo root (e.g. in CI), it uses this file.
// When invoked from frontend/ (e.g. `npm run lint`), it uses frontend/eslint.config.js.
module.exports = [
  {
    ignores: [
      '**/node_modules/**',
      'frontend/dist/**',
      // frontend/eslint.config.js uses ESM import/export syntax; skip it here
      // (it is properly handled when ESLint runs from within frontend/).
      'frontend/eslint.config.js',
    ],
  },
]

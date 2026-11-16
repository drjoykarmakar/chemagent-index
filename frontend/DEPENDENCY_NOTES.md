# Dependency notes

The lockfile is the reproducible frontend dependency source. The scoped override for `@typescript-eslint/typescript-estree` pins `minimatch` 11.0.8 to resolve a reported development-tool glob denial-of-service advisory. ESLint, TypeScript and the production build passed after this override. Reassess it when updating typescript-eslint; do not remove it while the resolved dependency remains vulnerable. Node 22+ satisfies the patched dependency's supported engine range.

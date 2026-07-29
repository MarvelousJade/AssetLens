# Repository maintenance

Before finishing a coding session:

- Remove unused code and imports after verifying they have no runtime, framework, migration, or test references.
- Delete commented-out code; preserve rationale in documentation or a concise explanatory comment when it is still useful.
- Consolidate duplicated behavior into a well-named helper when doing so makes ownership and testing clearer.
- Never commit credentials or runtime environment files. Keep `.env*` ignored and use `.env.example` only for safe placeholders.
- Run the relevant lint, type, test, and build checks, then inspect the final diff for generated files and secrets.

# Changelog

## 0.2.0

- **Anti-slop checker** (`skills/anti-slop-review`): 22 tropes (was 19). New info-level candidates for cream backgrounds, coloured glows and decorative stripes, found by reading CSS values. Declarations are now read only inside style regions: `<style>` blocks, `style` attributes, plain CSS files and tagged template literals from styled-components and emotion (including nested interpolations and arrow-function generics). Mask declarations are excluded one by one, `--skip-tropes` and an in-file `anti-slop-skip` comment skip chosen rules, and scanning time stays linear on large files. 419 tests (was 135).
- **Craft rules** (`skills/starter-components/craft`): new `interaction` module for working screens (app, system, migrate): fewer options, a designed last step, familiar conventions, defaults only for settings that can be changed back, and warnings that name a real consequence. Factual records (inspection results, measurements, sign-offs) are never pre-filled. `/fe-design` loads it by default for utility-type work.
- **Data-page design basis** (`references/info-dashboard-basis.md`) is now v1.1: a fifth required element, "honest data" (zeros, missing values, change values, comparison base, totals that add up); colour only signals good or bad when the metric has a stated criterion; KPI sparklines are no longer a default. `/fe-design` asks for a three-line note before designing an `app` screen and, in `app` mode, takes a business-object inventory instead of the showcase-style material inventory. The `Dashboard` and `Empty State` rows in `scene-templates.md` follow the same idea.
- Wording: the commands and skill descriptions now call the check "去 AI 味 (anti-slop)".

## 0.1.0

First public release.

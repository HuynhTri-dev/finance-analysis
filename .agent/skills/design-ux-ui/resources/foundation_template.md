<!--
  name: foundation_template.md
  description: Design Foundation Template — Design Tokens for [Project Name].
               Fill in all [PLACEHOLDER] values before starting UI design work.
               This file is the single source of truth for all visual tokens.
               Sync with the engineering team's CSS/Figma variable definitions.
-->

# Design Foundation — [Project Name]

> **Status:** `[ ] Draft` / `[ ] In Review` / `[ ] Approved`
> **Last Updated:** YYYY-MM-DD
> **Author:** [Designer Name]
> **Color Harmony:** `[ ] Monochromatic` / `[ ] Analogous` / `[ ] Complementary` / `[ ] Split-Complementary` / `[ ] Triadic` / `[ ] Tetradic`

---

## 1. Colors

> **Rule:** Never use raw HEX values directly in components. Always reference a named token.
> Run `node scripts/contrast_checker.js <bg> <fg>` to verify all text/background pairs meet WCAG 2.1 AA (≥ 4.5:1).

### 1.1 — Brand Palette

The core brand colors. Derive tints (+white) and shades (+black) at 10% increments.

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-brand-primary` | `#______` | Primary actions, links, key highlights |
| `--color-brand-primary-hover` | `#______` | 10% darker than primary — hover state |
| `--color-brand-primary-subtle` | `#______` | 20% opacity tint — selected backgrounds, tags |
| `--color-brand-secondary` | `#______` | Gradient accents, secondary CTA |
| `--color-brand-secondary-hover` | `#______` | 10% darker than secondary — hover state |

### 1.2 — Semantic / Feedback Colors

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-success` | `#______` | Success states, confirmations, completed steps |
| `--color-success-subtle` | `#______` | Success background (toast, banner) |
| `--color-warning` | `#______` | Warnings, degraded states, attention needed |
| `--color-warning-subtle` | `#______` | Warning background |
| `--color-error` | `#______` | Errors, destructive actions, validation failures |
| `--color-error-subtle` | `#______` | Error background (input field, inline message) |
| `--color-info` | `#______` | Informational notices, tips |
| `--color-info-subtle` | `#______` | Info background |

### 1.3 — Neutral Palette

| Token | HEX | Usage |
|-------|-----|-------|
| `--color-surface-bg` | `#______` | App/page background |
| `--color-surface-card` | `#______` | Card, panel, modal backgrounds |
| `--color-surface-overlay` | `#______` | Overlay/scrim behind modals |
| `--color-border` | `#______` | Dividers, input borders, separators |
| `--color-border-strong` | `#______` | Emphasized borders, focus rings |
| `--color-text-primary` | `#______` | Headings, primary body text |
| `--color-text-secondary` | `#______` | Supporting text, descriptions |
| `--color-text-muted` | `#______` | Labels, placeholders, hints, metadata |
| `--color-text-on-primary` | `#______` | Text on top of brand-primary background |
| `--color-text-disabled` | `#______` | Disabled state text |

### 1.4 — Contrast Verification Log

> Document contrast results here after running `contrast_checker.js`.

| Pair | Ratio | AA Normal | AA Large | AAA |
|------|-------|-----------|----------|-----|
| `text-primary` on `surface-bg` | `:1` | `[ ]` | `[ ]` | `[ ]` |
| `text-primary` on `surface-card` | `:1` | `[ ]` | `[ ]` | `[ ]` |
| `text-on-primary` on `brand-primary` | `:1` | `[ ]` | `[ ]` | `[ ]` |
| `text-muted` on `surface-bg` | `:1` | `[ ]` | `[ ]` | `[ ]` |
| [Add more pairs as needed] | `:1` | `[ ]` | `[ ]` | `[ ]` |

---

## 2. Typography

> **Rule:** Max 2 typeface families per system. Use font weight for emphasis — not color or extra fonts.

### 2.1 — Font Families

| Role | Font Family | Fallback Stack | Source |
|------|------------|----------------|--------|
| **Display / Heading** | `[Font Name]` | `system-ui, sans-serif` | Google Fonts / Self-hosted |
| **Body / UI** | `[Font Name]` | `system-ui, sans-serif` | Google Fonts / Self-hosted |
| **Monospace / Code** | `[Font Name]` | `'Courier New', monospace` | Google Fonts / Self-hosted |

> **Selection rationale:** [Explain why these fonts were chosen — e.g., "Geometric sans-serif chosen for SaaS product; conveys precision and modernity."]

### 2.2 — Type Scale

Base size: `16px (1rem)` — Scale ratio: `1.25` (Major Third)

| Token | rem | px equiv | Weight | Line-height | Usage |
|-------|-----|----------|--------|-------------|-------|
| `--text-display` | `3.052rem` | `~49px` | 800 | 1.1 | Hero / landing page titles |
| `--text-h1` | `2.441rem` | `~39px` | 700 | 1.1 | Page titles |
| `--text-h2` | `1.953rem` | `~31px` | 700 | 1.2 | Section headers |
| `--text-h3` | `1.563rem` | `~25px` | 600 | 1.2 | Card headers, sub-sections |
| `--text-h4` | `1.25rem`  | `~20px` | 600 | 1.3 | Minor headers, sidebar titles |
| `--text-body-lg` | `1rem` | `16px` | 400 | 1.6 | Primary body text |
| `--text-body-sm` | `0.875rem` | `14px` | 400 | 1.5 | Secondary text, descriptions |
| `--text-label` | `0.75rem` | `12px` | 500 | 1.4 | Form labels, badges, captions |
| `--text-code` | `0.875rem` | `14px` | 400 | 1.6 | Code blocks, technical output |

### 2.3 — Font Weights Available

| Weight | Name | Usage |
|--------|------|-------|
| 400 | Regular | Body text, descriptions |
| 500 | Medium | Labels, emphasized UI text |
| 600 | Semi-Bold | Sub-headings, table headers |
| 700 | Bold | Headings, CTAs |
| 800 | Extra-Bold | Display / Hero text |

### 2.4 — Line Length Rule

> Constrain all reading text containers to **45–75 characters** per line.
> Apply `max-width: 65ch` on body text blocks in CSS.

---

## 3. Grid & Spacing

### 3.1 — Responsive Breakpoints

| Name | Min Width | Max Width | Columns | Gutter | Margin |
|------|-----------|-----------|---------|--------|--------|
| `xs` — Mobile | 0px | 599px | 4 | 16px | 16px |
| `sm` — Mobile L | 600px | 767px | 4 | 16px | 24px |
| `md` — Tablet | 768px | 1023px | 8 | 24px | 32px |
| `lg` — Desktop | 1024px | 1279px | 12 | 24px | 48px |
| `xl` — Wide | 1280px | 1535px | 12 | 32px | 64px |
| `2xl` — Ultra-wide | 1536px+ | — | 12 | 32px | 80px |

### 3.2 — Spacing Scale (8-Point Grid)

> **Rule:** All margin, padding, gap values MUST be multiples of 8.
> **Exception (4pt sub-grid):** Multiples of 4 allowed for micro-spacing inside dense components.

| Token | Value | Usage |
|-------|-------|-------|
| `--spacing-1` | `4px` | Sub-grid only — icon inner padding, micro gaps |
| `--spacing-2` | `8px` | Icon-to-label gap, tight inline spacing |
| `--spacing-3` | `16px` | Button padding (vertical), list item gap |
| `--spacing-4` | `24px` | Card internal padding, related content groups |
| `--spacing-5` | `32px` | Section separator, form group spacing |
| `--spacing-6` | `48px` | Large section gap, page margins (mobile) |
| `--spacing-7` | `64px` | Top-level layout margins (desktop) |
| `--spacing-8` | `80px` | Hero section padding |
| `--spacing-9` | `96px` | Full-page section padding |

**Gestalt Proximity — spacing communicates relationship:**

```
Label <-> Input field        →  8px   (tightly coupled)
Input <-> Next field group   →  24px  (related but distinct)
Section A <-> Section B      →  48px  (clearly separated)
```

### 3.3 — Border Radius

> **Nested Radius Formula (MANDATORY):** `Outer radius = Inner radius + Padding between them`

| Token | Value | Tone | Usage |
|-------|-------|------|-------|
| `--radius-none` | `0px` | Rigid/Technical | Table cells, flush-edge elements |
| `--radius-xs` | `4px` | Structured | Checkboxes, small tags, tooltips |
| `--radius-sm` | `8px` | Professional | Cards, modals, inputs, dropdowns |
| `--radius-md` | `12px` | Modern-Friendly | Feature cards, highlighted panels |
| `--radius-lg` | `16px` | Friendly | Banners, large images, drawers |
| `--radius-xl` | `24px` | Approachable | Marketing cards, onboarding panels |
| `--radius-full` | `9999px` | Playful/Prominent | Pill buttons, avatars, badges, search |

> **Project choice:** Base radius = `___px` — Applied to: Cards / Modals / Inputs

---

## 4. Iconography

### 4.1 — Icon Library

| Setting | Value |
|---------|-------|
| **Library** | [e.g., Lucide Icons, Phosphor, Material Symbols, Heroicons, Custom SVG] |
| **Style** | `[ ] Outline` / `[ ] Filled` / `[ ] Duotone` — choose ONE, use consistently |
| **Stroke width** | `___px` (1.5px = fine/modern, 2px = standard/accessible) |

### 4.2 — Icon Size Scale

> All icon bounding boxes must be multiples of 8. Never transform icons with non-standard CSS scales.

| Size Name | Bounding Box | Usage |
|-----------|-------------|-------|
| `--icon-xs` | `12x12px` | Inline text decorators, breadcrumb arrows |
| `--icon-sm` | `16x16px` | Inside input fields, compact menus |
| `--icon-md` | `20x20px` | Standard buttons, list items |
| `--icon-lg` | `24x24px` | Navigation items, primary actions |
| `--icon-xl` | `32x32px` | Feature highlights, section icons |
| `--icon-2xl` | `48x48px` | Empty states, onboarding illustrations |

### 4.3 — Usage Rules

- **Accessibility:** Icons used alone (no visible text label) MUST have `aria-label` or a visible tooltip.
- **Color:** Icons use `currentColor` — do not hardcode icon colors outside of text tokens.
- **Touch target:** Interactive icons must have a minimum touch target of `44x44px` (WCAG 2.5.5). Use padding — do not enlarge the icon itself.

---

## 5. Elevation & Shadows

> **Concept:** Elevation communicates Z-axis hierarchy. Higher elevation = visually closer to the user = more dominant.

### 5.1 — Shadow Scale

| Level | Token | CSS Value | Used For |
|-------|-------|-----------|----------|
| 0 — Flat | `--shadow-0` | `none` | In-page content, flat cards, table rows |
| 1 — Raised | `--shadow-1` | `0 1px 3px rgba(0,0,0,.12), 0 1px 2px rgba(0,0,0,.08)` | Inactive cards, list items |
| 2 — Floating | `--shadow-2` | `0 4px 6px rgba(0,0,0,.10), 0 2px 4px rgba(0,0,0,.08)` | Active cards, dropdowns, date pickers |
| 3 — Overlay | `--shadow-3` | `0 10px 20px rgba(0,0,0,.12), 0 4px 8px rgba(0,0,0,.08)` | Sticky headers, floating action buttons |
| 4 — Modal | `--shadow-4` | `0 20px 40px rgba(0,0,0,.16), 0 8px 16px rgba(0,0,0,.10)` | Modal dialogs, side drawers |
| 5 — Max | `--shadow-5` | `0 32px 64px rgba(0,0,0,.20), 0 16px 32px rgba(0,0,0,.12)` | Notification toasts, system alerts |

### 5.2 — Z-Index Scale

> **Rule:** Never use arbitrary z-index values (z-index: 9999). Always use a named token.

| Token | Value | Layer | Examples |
|-------|-------|-------|---------|
| `--z-base` | `0` | Base | Normal page content |
| `--z-raised` | `10` | Raised | Sticky table headers, pinned columns |
| `--z-dropdown` | `100` | Overlay | Dropdowns, autocomplete, tooltips |
| `--z-sticky` | `200` | Sticky | Sticky nav/header, persistent sidebars |
| `--z-modal` | `300` | Modal | Dialog overlays, side drawers |
| `--z-toast` | `400` | Toast | Notification toasts, snackbars |
| `--z-max` | `500` | System | Critical alerts, full-screen overlays |

---

## 6. Motion & Animation

> **Rule:** Animation must serve a functional purpose. Never animate purely for decoration.

| Token | Duration | Easing | Usage |
|-------|----------|--------|-------|
| `--motion-instant` | `0ms` | — | Immediate state changes, no transition |
| `--motion-fast` | `100ms` | `ease-out` | Hover states, icon swaps |
| `--motion-default` | `200ms` | `ease-in-out` | Button presses, toggle switches |
| `--motion-moderate` | `300ms` | `ease-in-out` | Dropdowns, panel expansions |
| `--motion-slow` | `500ms` | `ease-in-out` | Modal entry, page transitions |

> **Accessibility:** Always honor `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    transition-duration: 0ms !important;
    animation-duration: 0ms !important;
  }
}
```

---

## Approval & Sign-off

| Role | Name | Status | Date |
|------|------|--------|------|
| Lead Designer | | `[ ] Approved` | |
| Frontend Lead | | `[ ] Approved` | |
| Product Manager | | `[ ] Approved` | |

---

*Foundation Version: 1.0.0 | Project: [Project Name] | Design System: [System Name]*

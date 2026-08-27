---
name: ux-ui-analysis-design
description: >
  A comprehensive skill for UX/UI Analysis and Design. Activates when the user
  requests wireframes, mockups, design system tokens, user flows, heuristic
  evaluations, accessibility audits, or dev-handoff annotations. Guides the
  agent through a structured, principle-driven design process rooted in the
  C.R.A.P. UI framework and the 12 core UX principles, tailored for
  enterprise-grade web applications.
triggers:
  - "create wireframe"
  - "generate mockup"
  - "create design system for ux/ui"
  - "evaluate accessibility"
  - "component design"
  - "phân tích UX"
  - "thiết kế UI"
  - "phân tích giao diện"
  - "review UI"
  - "audit UX/UI"
  - "đánh giá UX/UI"
  - "kiểm thử accessibility"
  - "báo cáo UX/UI"
---

# Skill: UX/UI Analysis & Design

## Overview

This skill provides a structured, end-to-end workflow for UX/UI analysis and design tasks. It is grounded in two foundational design frameworks:

1. **C.R.A.P.** — 4 foundational UI principles (Contrast, Repetition, Alignment, Proximity).
2. **12 Core UX Principles** — human-centered principles that govern user experience quality.

## When to Use This Skill
- Use this skill when the user explicitly requests to create wireframes, mockups, design systems, or conduct UX audits.
- Especially helpful for establishing visual hierarchy, color tokens, and accessibility compliance.
- **Do NOT use** when the user simply asks to "read", "summarize", or "open" an existing UX/UI document without asking for new designs or audits.

## Core Knowledge Base

### 1.1 — The C.R.A.P. UI Principles

The four foundational principles of visual interface design. Apply all four to every screen you design or review.

| # | Principle | Core Idea | Practical Application |
|---|-----------|-----------|----------------------|
| 1 | **Contrast** | Use differences in color, size, and weight to create hierarchy and focal points. | Ensure primary CTAs have high contrast ratios (>= 4.5:1 for WCAG AA). Use bold weight for headings. Never use similar shades for competing elements. |
| 2 | **Repetition** | Repeat visual patterns (layout, color, icon style) to build consistency. | Define a design system with tokens. Reuse the same card component, button style, and spacing scale across all screens. |
| 3 | **Alignment** | Organize elements along invisible axes to create order and rhythm. | Use a 12-column grid. Align text to a baseline grid. Never place elements arbitrarily -- every item must align with something else. |
| 4 | **Proximity** | Group related items together to communicate their relationship. | Use consistent spacing: tight gaps (8px) for related items, larger gaps (24-32px) to separate sections. Labels must be proximate to their fields. |

### 1.2 — The 13 Core UX Principles

Apply these principles during design decisions, heuristic evaluations, and design critiques.

| # | Principle | Definition | Enterprise AI Context Example |
|---|-----------|------------|-------------------------------|
| 1 | **User Centricity** | Place user needs, behaviors, and emotions at the center of every decision. | Design the chat interface around the mental model of "asking a colleague," not a search engine. |
| 2 | **Clarity & Simplicity** | Reduce cognitive load. Remove non-essential elements, simplify steps. | Show only one primary action per screen. In the Admin UI, surface the most critical unresolved queries first. |
| 3 | **Consistency** | Maintain uniform visual language and interaction patterns product-wide. | A "Source Citation" badge looks and behaves identically whether it appears in a chat reply or a report view. |
| 4 | **Feedback** | Provide timely visual, auditory, or haptic signals confirming system state. | Show a real-time "Agent thinking..." spinner with agent name. Display a progress tracker for multi-step queries. |
| 5 | **Accessibility** | Design inclusively for users with visual, auditory, or motor disabilities. | All WCAG 2.1 AA compliance. Keyboard-navigable admin panel. Screen-reader-compatible data tables and charts. |
| 6 | **Visual Hierarchy** | Guide attention through size, color, and positioning. | In a chat reply: Answer text (large) → Source citations (smaller) → Confidence score (smallest, muted color). |
| 7 | **Usability** | Ensure users can complete goals efficiently with minimal friction. | The chat input should be the most prominent element on the user screen. Query submission must be <= 2 clicks. |
| 8 | **Flexibility & Efficiency** | Support both novice users and power users with shortcuts and advanced options. | Provide suggested prompts for new users; support slash-commands (/report, /filter) for power users. |
| 9 | **Aesthetic Minimalism** | Show only what is necessary. Use whitespace deliberately. | Collapse source citations behind a toggle by default. Do not render charts unless the user's query requests data visualization. |
| 10 | **Error Prevention & Recovery** | Prevent mistakes and make recovery trivial. | Before clearing a conversation, show a confirmation dialog. On API errors, display a "Retry" button with error context. |
| 11 | **Mobile Responsiveness** | Adapt seamlessly across screen sizes without loss of functionality. | The chat UI must be fully functional on tablet screens (>= 768px). Admin UI may gracefully degrade on mobile. |
| 12 | **Task-Oriented Design** | Guide users through tasks step-by-step, eliminating distractions. | The Admin "Knowledge Review" flow is a linear wizard: Review → Edit Answer → Assign Domain → Publish. |
| 13 | **Learnability** | Leverage familiar patterns so new users onboard instantly. | Use a chat-bubble UI (familiar from messaging apps). Provide an interactive onboarding tour on first login. |

## Step-by-Step Instruction

### Step 1 — Discovery & Research

**Goal:** Understand context before drawing anything.

**Checklist:**
- [ ] **Context Gathering:** Check for existing project documentation (e.g., scope, personas, objectives, use cases).
  - *If structured files exist (e.g., in `1-project/` or `2-usecase/`), read them.*
  - *If they DO NOT exist, ask the user to provide this context or infer it from the initial prompt.*
- [ ] Identify the platform: Web App, Mobile, Desktop.
- [ ] Identify constraints: light/dark mode, accessibility level, responsive breakpoints.
- [ ] Define the **design objective** in one sentence before proceeding.

**Output:** A brief `discovery_summary.md` listing:
  - Primary user persona for this screen/flow.
  - Core task the user must complete.
  - Key constraints.


### Step 2 — Information Architecture (IA)

**Goal:** Define structure before visual design.

**Tasks:**
1. Map the **navigation structure** (sidebar, top nav, breadcrumbs).
2. Define the **content hierarchy** for each screen:
   - What is the #1 piece of information? (Primary)
   - What supports it? (Secondary)
   - What is contextual/optional? (Tertiary)
3. Group related content using **Proximity** (C.R.A.P. Principle 4).
4. Validate the IA against the user's mental model (ask: "Would a new employee know where to find this?").

**Output:** A content hierarchy table per screen.

```markdown
| Priority  | Content Block        | Visible by Default? |
|-----------|----------------------|---------------------|
| Primary   | Chat input + Send    | Yes                 |
| Primary   | AI Response          | Yes                 |
| Secondary | Source citations     | Toggle (collapsed)  |
| Secondary | Agent routing path   | Toggle (collapsed)  |
| Tertiary  | Conversation history | Sidebar             |
| Tertiary  | User settings        | Top-right icon      |
```

---

### Step 3 — Design System Definition

**Goal:** Establish the visual language before building screens.

> **Rule:** Never design screens before the design system is defined. Screens must consume tokens, not invent ad-hoc styles.

#### 3.1 — Color Strategy

**Process (ask the user, do not decide for them):**

> "What is your product domain and who are your primary users?"

Based on the answer, recommend the appropriate color harmony from the table below, then ask the user to confirm a base color (HEX) before generating tokens.

| # | Harmony | Color Logic | Domain / Use Case | Target User |
|---|---------|-------------|-------------------|-------------|
| 1 | **Monochromatic** | One base hue + multiple tints, shades, tones of that same hue. | Healthcare, Enterprise ERP, Internal Finance | Professionals working long sessions — reduces cognitive load and eye strain. |
| 2 | **Analogous** | 3 adjacent hues on the color wheel (e.g., Blue → Teal → Green). | Education, Environment, Lifestyle & Wellness | Students and casual users seeking a smooth, non-aggressive visual experience. |
| 3 | **Complementary** | 2 opposite hues on the color wheel (e.g., Blue ↔ Orange). | HR/Recruitment, E-commerce, Marketing | Short-attention users — extreme contrast makes CTAs like "Apply" or "Buy" immediately pop. |
| 4 | **Split-Complementary** | 1 base hue + 2 hues adjacent to its direct complement. Less harsh than Complementary. | Tech Startups, MVPs, Consumer Mobile Apps | Young / tech-savvy users who need visual excitement but also need to read long content without strain. |
| 5 | **Triadic** | 3 hues forming an equilateral triangle on the color wheel (e.g., Red – Yellow – Blue). | Entertainment, Gaming, F&B, Creative Arts | Teenagers, children, users seeking high energy and playful interaction. |
| 6 | **Tetradic (Double-Complementary)** | 2 complementary pairs forming a rectangle on the color wheel. Complex — requires 1 dominant + 3 accent colors. | Smart Traffic, IoT Dashboards, Infrastructure Monitoring | Engineers and sysadmins who must distinguish many simultaneous states (normal, warning, danger, offline) on a dense screen. |

*References: Interaction Design Foundation (IxDF) – Color Theory in UI Design; Wikipedia – Color scheme.*

**After the user confirms their color harmony and base HEX:**
1. Derive a full semantic token set (primary, secondary, surface, text, status colors).
2. **Verify contrast before finalizing** — run the contrast checker CLI tool:
   ```bash
   node scripts/contrast_checker.js "<background-hex>" "<foreground-hex>"
   # Example:
   node scripts/contrast_checker.js "#1a1a2e" "#F1F5F9"
   # Target: >= 4.5:1 for AA (body text), >= 3:1 for AA Large, >= 7:1 for AAA
   # Exit code 0 = passes AA Normal Text, exit code 1 = fails
   ```
3. Document tokens using CSS custom property naming convention:
   ```
   --color-brand-primary, --color-surface-bg, --color-text-primary, --color-success, etc.
   ```

#### 3.2 — Typography Strategy

**Do NOT select fonts for the user.** Instead, guide them through these advisory questions:

> 1. "Does your product need to feel **modern & technical** (SaaS, dev tools) or **warm & human** (healthcare, education)?"
> 2. "Is the UI **data-dense** (many small numbers/labels) or **content-rich** (long-form reading)?"
> 3. "Do you prefer geometric letterforms (clean, minimal) or humanist letterforms (curved, approachable)?"

Based on answers, present 2–3 font pairing suggestions and let the user choose. Then generate the type scale.

**Typography System Rules (enforce regardless of font choice):**

| Rule | Specification | Rationale |
|------|--------------|----------|
| **Base body size** | Minimum **16px (1rem)** for body text on Web and Mobile | Ensures readability without zooming |
| **Line height (body)** | Minimum **1.5× (150%)** of font size | Prevents losing reading place |
| **Line height (headings)** | **1.1–1.2×** of font size | Keeps heading blocks compact |
| **Line length** | **45–75 characters** per line (incl. spaces) | Prevents eye fatigue and rhythm-breaking |
| **Max typefaces** | Maximum **2 typeface families** per system | 3+ fonts cause visual noise |
| **Creating emphasis** | Use **font weight** (Regular → Medium → Semi-Bold), NOT more colors/fonts | Weight creates hierarchy cleanly |

**Type Scale — derive using Major Third ratio (1.25×) from confirmed base:**

```
H1     = base × 1.25⁴  (≈ 2.44rem)
H2     = base × 1.25³  (≈ 1.95rem)
H3     = base × 1.25²  (≈ 1.56rem)
BodyLG = base × 1.25¹  (≈ 1.25rem)
BodyMD = base           (1rem / 16px)
BodySM = base ÷ 1.25   (≈ 0.8rem)
Label  = base ÷ 1.25²  (≈ 0.64rem) — use sparingly
```

#### 3.3 — Spacing & Border Radius

**Spacing — 8-Point Grid System:**

> All margin, padding, gap, and component height values MUST be multiples of 8. Never use arbitrary numbers (11px, 17px, 25px).

*Why 8?* Screens scale at 1×, 1.5×, 2×, 3× density. 8 divides perfectly across all densities — prevents sub-pixel blurring.

| Token | Value | Common Usage |
|-------|-------|------------------|
| `--spacing-xs`  | 8px  | Icon-to-label gap inside buttons |
| `--spacing-sm`  | 16px | Button vertical padding, list item spacing |
| `--spacing-md`  | 24px | Card padding, gap between related content blocks |
| `--spacing-lg`  | 32px | Section separator |
| `--spacing-xl`  | 48px | Large section gap, page margins |
| `--spacing-2xl` | 64px | Top-level layout margins |

> **Exception (4pt sub-grid):** For micro-spacing within dense components (icon inside badge), multiples of 4 are allowed: 4px, 12px, 20px.

**Gestalt Proximity Law — spacing creates hierarchy:**
- Label ↔ its Input: `8px`
- Input ↔ next field group: `24px`
- Section A ↔ Section B: `48px`

---

**Border Radius — Tone of Voice:**

| Value | Personality | Best For |
|-------|-------------|----------|
| 0px | Rigid, Technical | Dashboard tables, elements flush to screen edge |
| 4px | Neutral, Structured | Checkboxes, tags, tooltips |
| 8px | Modern & Professional | Cards, modals, inputs — Apple/Material standard |
| 16–24px | Friendly, Approachable | Education apps, CTAs, feature cards |
| 9999px (Pill) | Playful, Prominent | Primary buttons, avatars, search bars |

**Nested Radius Formula (mandatory when nesting components):**
```
Outer radius = Inner radius + Padding between them

Example: Image inner radius = 8px, Card padding = 16px
→ Card outer radius = 8 + 16 = 24px
```

*References: Google Material Design (Shapes & Layout); Apple Human Interface Guidelines.*

---

#### 3.4 — Core Component States

Define interaction states for every component — use token names, NOT hardcoded hex values:

```
Button — Primary:
  Normal:   bg=var(--color-brand-primary), text=var(--color-text-on-primary), radius=var(--radius-md)
  Hover:    bg darkened 10%, transition: 150ms ease
  Focus:    2px outline offset using a lighter tint of --color-brand-primary
  Disabled: opacity=50%, cursor=not-allowed
  Loading:  Spinner replaces label text

Input Field:
  Normal:   border=1px solid var(--color-border), bg=var(--color-surface-card)
  Focus:    border=2px solid var(--color-brand-primary)
  Error:    border=2px solid var(--color-error), error message below in --text-label size
  Disabled: opacity=60%, cursor=not-allowed
```

---

### Step 4 — Wireframing

**Goal:** Define layout structure without visual polish (low-fidelity).

**Rules:**
- Use only grayscale (black, white, grays).
- Focus on **layout, hierarchy, and flow** -- not colors or imagery.
- Apply all 4 C.R.A.P. principles to every wireframe.
- Annotate each wireframe with: element name, purpose, and interaction notes.

**Standard Wireframe Annotation Format:**
```markdown
[WF-001] Screen: User Chat Interface
- Navigation: Left sidebar (Conversation history) | Top bar (User info, Settings)
- Primary Zone: Full-height chat message feed (scrollable)
- Sticky: Bottom input bar with Send button
- Secondary: Collapsible "Sources" panel on right (desktop only)
- Error State: Inline banner below message if Agent fails
```

---

### Step 5 — High-Fidelity Mockup

**Goal:** Apply the design system to wireframes to produce pixel-perfect designs.

**Checklist:**
- [ ] Apply color tokens from Step 3.
- [ ] Apply typography scale from Step 3.
- [ ] Apply spacing scale (Base-8) consistently.
- [ ] Verify C.R.A.P. principles are visible in the final layout.
- [ ] Verify all 13 UX principles are upheld (use checklist in Part 3).
- [ ] Design all interactive states: Normal, Hover, Focus, Active, Disabled, Loading, Error, Empty.
- [ ] Produce designs for both Desktop (1440px) and Tablet (768px) breakpoints.

---

### Step 6 — Heuristic Evaluation & Accessibility Audit (UX Audit)

**Goal:** Critique an existing or newly designed interface against C.R.A.P. framework, 13 Core UX principles, and WCAG 2.1 AA accessibility standards.

> **Mandatory Template:** When conducting a UX/UI audit or review, strictly follow the format in [`resources/review_template.md`](.agent/skills/design-ux-ui/resources/review_template.md).
> 
> **Execution Steps:**
> 1. Run color contrast checks via `node .agent/skills/design-ux-ui/scripts/contrast_checker.js <bg> <fg>`.
> 2. Search codebase for `Semantics`, `aria-label`, `IconButton`, and touch target constraints.
> 3. Verify design token usage and detect raw widget vs common widget fragmentation.
> 4. Fill in all sections: C.R.A.P. Analysis (with Mermaid graph), 13 Core UX Principles table, Accessibility Audit (WCAG 2.1 AA), Heuristic Evaluation report table, and Actionable Roadmap.

**Severity Ratings:**

| Severity | Label | Meaning |
|----------|-------|---------|
| 0 | Not a problem | Debatable cosmetic issue |
| 1 | Cosmetic | Fix if time permits |
| 2 | Minor | Low-priority fix |
| 3 | Major | High-priority -- impacts task completion |
| 4 | Catastrophic | Must fix before launch |

---

### Step 7 — Developer Handoff Annotations

**Goal:** Ensure developers can implement designs precisely without guessing.

**Mandatory Annotations for Every Screen:**

1. **Layout:** Grid system, column count, gutter width, margin.
2. **Spacing:** Exact padding/margin values using spacing tokens.
3. **Typography:** Exact token name for every text element.
4. **Colors:** Exact token name (never bare hex) for every colored element.
5. **Interaction Behavior:** What happens on hover, click, focus, error.
6. **Motion:** Transition duration, easing function, trigger.
7. **Responsive Rules:** Which elements hide/reflow at each breakpoint.
8. **Edge Cases:** Empty state, loading state, error state, max-content state.

**Annotation Example:**
```markdown
[Component: Chat Input Bar]
- Height: 56px (fixed)
- Position: Sticky, bottom-0, full-width
- bg: var(--color-surface-card)
- border-top: 1px solid var(--color-border)
- Input: flex-grow, height=40px, padding=8px 16px
- Send Button: width=40px, height=40px, icon-only on mobile
- Interaction: Pressing Enter sends message; Shift+Enter inserts newline
- Disabled state: While AI is generating a response, input is disabled
- Transition: Button icon animates from Send → Stop when AI is responding
```

---

## Part 3: Principle Compliance Checklist

Use this checklist at the end of Step 5 (Mockup) and Stepư 6 (Audit).

```markdown
## UX/UI Compliance Checklist — [Screen Name]

### C.R.A.P. UI Principles
- [ ] CONTRAST: Primary actions have sufficient contrast (>= 4.5:1). Visual hierarchy is evident.
- [ ] REPETITION: Components are consistent. Same element looks identical across screens.
- [ ] ALIGNMENT: All elements align to the grid. No arbitrary positioning.
- [ ] PROXIMITY: Related items are grouped. Unrelated items are separated by adequate spacing.

### UX Principles
- [ ] User Centricity: Design solves the user's primary task, not the business's convenience.
- [ ] Clarity & Simplicity: No unnecessary elements. One primary action per view.
- [ ] Consistency: Terminology, icons, and patterns match across the product.
- [ ] Feedback: Every user action has a visible system response.
- [ ] Accessibility: WCAG 2.1 AA compliant. Keyboard navigable. Screen-reader labels present.
- [ ] Visual Hierarchy: The user's eye is guided to the most important element first.
- [ ] Usability: Core task completion requires <= 3 clicks/taps.
- [ ] Flexibility & Efficiency: Power-user shortcuts exist where applicable.
- [ ] Aesthetic Minimalism: No decorative elements that serve no functional purpose.
- [ ] Error Prevention & Recovery: Destructive actions are confirmed. Errors are recoverable.
- [ ] Mobile Responsiveness: Verified on 768px (tablet) breakpoint.
- [ ] Task-Oriented Design: Complex flows use a step-by-step wizard pattern.
- [ ] Learnability: UI patterns are familiar (follows OS/platform conventions).
```

---

## Part 4: Quick Reference — Design Decisions

Use these as heuristics when making fast design decisions.

| Situation | Recommended Approach |
|-----------|---------------------|
| Two competing CTAs on one screen | Primary = filled button, Secondary = outline button. Never two filled. |
| Form with many fields | Group fields by topic using proximity + labeled sections. Use progressive disclosure. |
| Data table with 10+ columns | Freeze first column. Allow user to customize visible columns. |
| Long AI response | Auto-expand with a "Read more" toggle. Never truncate silently. |
| Destructive action (Delete, Clear) | Always require explicit confirmation. Use red color for the confirm button only. |
| Empty state | Never show a blank white screen. Show illustration + helpful message + suggested action. |
| Loading state (>2 seconds) | Show a skeleton screen, not a spinner. Display partial content as it arrives. |
| Error state | Explain what happened + why + what to do next. Never show raw error codes to end users. |
| Navigation with 5+ items | Use icons + labels. Collapse to icon-only on smaller breakpoints. |
| Dashboard with multiple metrics | Lead with the single most important KPI. Group secondary metrics in cards below. |

---

## Part 5: Design File Structure

When creating design documentation for a project, follow this directory structure.

```
/AgentWorkspace
├── 1-project/
│   ├── 1-project_scope.md       # Project goals and scope
│   ├── 2-user_personas.md       # User archetypes and needs
│   └── 3-design_object.md       # Design objectives and success metrics
├── 2-usecase/
│   ├── user_flows.md            # Task flows per persona
│   └── use_cases.md             # Detailed use case scenarios
├── 3-design_system/
│   ├── color_tokens.md          # Semantic color definitions
│   ├── typography.md            # Type scale and rules
│   ├── spacing.md               # Spacing scale and usage
│   └── components.md            # Component library definitions
├── 4-UI_design/
│   ├── wireframes/              # Low-fidelity layout sketches
│   ├── mockups/                 # High-fidelity screen designs
│   └── handoff/                 # Developer annotation files
├── resources/
│   ├── foundation_template.md   # Design tokens foundation template
│   └── review_template.md       # UX/UI & Accessibility audit report template
├── scripts/
│   └── contrast_checker.js      # WCAG contrast ratio calculation script
└── SKILL.md                     # This skill file
```

---

*Skill Version: 1.0.0 | Last Updated: 2026-08-16 | Author: AgentWorkspace*

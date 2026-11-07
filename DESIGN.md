---
name: CivicFix
description: AI-Powered City Infrastructure Reporting & Operations Platform — Maryland Flag Liquid Glass Edition
colors:
  white: "#FFFFFF"
  white-warm: "#FFFDF7"
  gold: "#FFC72C"
  gold-tint-glass: "rgba(255, 199, 44, 0.22)"
  red: "#E03A3E"
  red-tint-glass: "rgba(224, 58, 62, 0.16)"
  black: "#0B0B0C"
  black-tint-glass: "rgba(11, 11, 12, 0.08)"
  black-muted: "rgba(11, 11, 12, 0.60)"
  black-subtle: "rgba(11, 11, 12, 0.38)"
  black-border: "rgba(11, 11, 12, 0.08)"
  black-border-strong: "rgba(11, 11, 12, 0.16)"
  
  # Semantic Mapping
  surface-canvas: "#FFFFFF"
  surface-canvas-warm: "#FFFDF7"
  surface-card: "#FFFFFF"
  surface-card-subtle: "#FFFDF7"
  text-primary: "#0B0B0C"
  text-secondary: "rgba(11, 11, 12, 0.72)"
  text-muted: "rgba(11, 11, 12, 0.60)"
  action-primary: "#E03A3E"
  action-accent: "#FFC72C"
  border-default: "rgba(11, 11, 12, 0.08)"
  border-glass-inner: "rgba(255, 255, 255, 0.90)"
  border-glass-outer: "rgba(11, 11, 12, 0.08)"
typography:
  font-family-sans: "Public Sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
  font-family-display: "Public Sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
  font-family-mono: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
  display:
    fontFamily: "Public Sans, sans-serif"
    fontSize: "3.25rem"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  heading-1:
    fontFamily: "Public Sans, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 750
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  heading-2:
    fontFamily: "Public Sans, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Public Sans, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0em"
  caption:
    fontFamily: "Public Sans, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.02em"
rounded:
  xs: "6px"
  sm: "10px"
  md: "14px"
  lg: "20px"
  xl: "28px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.red}"
    textColor: "{colors.white}"
    rounded: "{rounded.md}"
    padding: "12px 24px"
  button-accent:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.black}"
    rounded: "{rounded.md}"
    padding: "12px 24px"
  button-secondary-glass:
    backgroundColor: "rgba(255, 255, 255, 0.68)"
    textColor: "{colors.black}"
    rounded: "{rounded.md}"
    padding: "12px 24px"
---

# Design System — CivicFix (Maryland Flag Liquid Glass Edition)

## 1. Brand Palette & The 60/15/12/13 Distribution Rule

Strictly limited to four hues plus their neutral tints/shades. **No purple, blue, teal, or green anywhere.**

```
┌────────────────────────────────────────────────────────┐
│  WHITE / WARM WHITE: ~60% (Canvas, Cards, Sheets)      │
├────────────────────┬───────────────────┬───────────────┤
│  GOLD: ~15%        │  BLACK: ~13%      │  RED: ~12%    │
│  (Active, Badges)  │  (Text, Dividers) │  (Action/Alert)│
└────────────────────┴───────────────────┴───────────────┘
```

1. **White (`#FFFFFF`) & Warm White (`#FFFDF7`) — ~60% Area**:
   - The absolute dominant ground. White represents municipal transparency and daylight outdoor clarity.
   - Used for the viewport base, solid reading cards, sheets, and dialog surfaces.
2. **Gold / Yellow (`#FFC72C`) — ~15% Area**:
   - Represents civic energy, active selection, status highlights, telemetry badges, and interactive gold glass tabs.
   - **Text Rule**: ALWAYS paired with Black (`#0B0B0C`) text. NEVER white text on gold, and NEVER gold text on white.
3. **Black (`#0B0B0C`) — ~13% Area**:
   - High-contrast text, icon outlines, fine 1px structural borders, and custom UI handles.
   - In light mode, neutral grays are derived purely as tints of black (`rgba(11, 11, 12, 0.08)` to `0.72`).
   - Serves as the deep base canvas in Dark Mode.
4. **Red (`#E03A3E`) — ~12% Area**:
   - **STRICT SEMANTIC RULE**: Red is reserved for **Urgency / Critical Priority** and **Primary Action Buttons ("Submit Report") ONLY**.
   - **NEVER** use Red for "Resolved", completed tasks, or positive success states.

---

## 2. Unified Status and Color Semantics System (WCAG 1.4.1 Compliant)

Every status throughout CivicFix must be distinguishable **without color alone** via a triple redundancy system: **Shape + Icon + Text Label**.

| Status State | Shape Geometry | Icon Glyph | Color Assignment | Accessibility / Semantic Meaning |
| :--- | :--- | :--- | :--- | :--- |
| **Submitted / Open** | Outlined Ring | Circle (`○`) | Neutral Black (`#0B0B0C`) with subtle gray background | New report logged, awaiting municipal triage. |
| **In Progress** | Half-Filled Ring | Clock / Dot (`◑`) | Maryland Gold (`#FFC72C`) badge with Black text | Active work order assigned, crew dispatched. |
| **Resolved** | Solid Rounded Check | Checkmark Circle (`✓`) | Solid Black (`#0B0B0C`) icon on clean white/black-06 | Work verified and completed. **NO RED.** |
| **Critical / Urgent** | Sharp Diamond / Shield | Alert Triangle (`▲ !`) | Solid Maryland Red (`#E03A3E`) badge with White text | Immediate safety or structural hazard. |

---

## 3. Map Pin Priority Shape & Style System

Map pins must never rely solely on color. Each severity and lifecycle stage has a **distinct geometric shape**:

```
Critical/Urgent:       Normal/Medium:         Low Priority:          Resolved:
    ▲                      ●                      ○                      ■
  / ! \                  / ● \                  /   \                  [ ✓ ]
  \   /                  \   /                  \   /                  [   ]
    ▼                      ▼                      ▼                      ▼
(Red Diamond)          (Gold Teardrop)        (White Circle)         (Black Hexagon)
```

1. **Critical / High Priority**:
   - **Shape**: Rotated Diamond with an embedded exclamation mark (`!`).
   - **Color**: Solid Maryland Red (`#E03A3E`) fill, black outline, white glyph.
   - **Behavior**: Subtle pulse ring on hover/selection.
2. **Medium / Normal Priority**:
   - **Shape**: Classic Teardrop with an embedded concentric circle.
   - **Color**: Solid Maryland Gold (`#FFC72C`) fill, black outline, black glyph.
3. **Low / Advisory**:
   - **Shape**: Circular Pin with white interior, black outline, and subtle center dot.
4. **Resolved**:
   - **Shape**: Hexagonal Badge with an embedded checkmark (`✓`).
   - **Color**: Solid Black (`#0B0B0C`) fill with white checkmark. Shows that the fix is verified.

---

## 4. Liquid Glass on White: The Two-Layer Architecture

### Layer 0: Solid Content Canvas (Bottom)
- Body text, report feeds, workflow steps, data metrics, and Leaflet/Google map frames sit on **solid white surfaces** (`#FFFFFF` with `#FFFDF7` card elevation).
- **Absolute Rule**: Body content, text cards, and forms NEVER use glass.

### Layer 1: Floating Translucent Glass (Top)
- Reserved exclusively for floating control chrome:
  - Sticky Top Header (`GlassNavBar`)
  - Bottom Mobile Tab Bar (`GlassTabBar`)
  - Floating Map Toolbars & Filter Bars
  - Floating Action Buttons (`GlassButton`)
  - Sliding Confirmation Sheets (`GlassSheet`)
- **Physical Glass Recipe on White**:
  - Base fill: `rgba(255, 255, 255, 0.55)` to `rgba(255, 255, 255, 0.72)`
  - Backdrop filter: `blur(20px) saturate(160%)`
  - Specular inner highlight: `inset 0 1px 0 0 rgba(255, 255, 255, 0.95)`
  - Defining outer edge: `1px solid rgba(11, 11, 12, 0.08)`
  - Ambient diffuse shadow: `0 8px 32px -4px rgba(11, 11, 12, 0.10), 0 2px 6px -1px rgba(11, 11, 12, 0.04)`

---

## 5. Normative Contrast Matrix (WCAG 2.1 AA Compliance)

| Text Color | Surface / Background | Contrast Ratio | WCAG AA Normal ($\ge 4.5:1$) | WCAG AA Large / Bold ($\ge 3.0:1$) | Status & Rules |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Black (`#0B0B0C`)** | White Canvas (`#FFFFFF`) | **19.8:1** | PASS (AAA) | PASS (AAA) | **Permitted**: Primary body text, labels, headings |
| **Black (`#0B0B0C`)** | Warm White (`#FFFDF7`) | **19.5:1** | PASS (AAA) | PASS (AAA) | **Permitted**: Card and sheet body content |
| **Black (`#0B0B0C`)** | Gold Solid (`#FFC72C`) | **12.4:1** | PASS (AAA) | PASS (AAA) | **Permitted**: Gold buttons, badges, active tabs |
| **Black (`#0B0B0C`)** | White Glass (`rgba(255,255,255,0.68)`) | **19.8:1** | PASS (AAA) | PASS (AAA) | **Permitted**: Floating navigation links, glass buttons |
| **White (`#FFFFFF`)** | Red Solid (`#E03A3E`) | **4.92:1** | PASS (AA) | PASS (AAA) | **Permitted**: Primary CTA buttons ("Submit Report") |
| **White (`#FFFFFF`)** | Black Solid (`#0B0B0C`) | **19.8:1** | PASS (AAA) | PASS (AAA) | **Permitted**: Dark mode body, dark footer bands, resolved badges |
| **Gold (`#FFC72C`)** | White (`#FFFFFF`) | **1.60:1** | **FAIL** | **FAIL** | 🚫 **STRICT BANS / BUILD FAIL (Never Gold on White)** |
| **White (`#FFFFFF`)** | Gold (`#FFC72C`) | **1.60:1** | **FAIL** | **FAIL** | 🚫 **STRICT BANS / BUILD FAIL (Never White on Gold)** |

# Design System

## 1. Overview

A confident, modern, and highly usable visual language.

The interface should be:

- Clean
- Roomy
- Structured
- Professional
- Readable
- Consistent

The foundation should remain quiet. Most surfaces should stay white or very light gray, while emphasis should come from hierarchy, spacing, typography, and small color accents rather than heavy decoration.

Color should be used sparingly and with clear semantic meaning.

---

# 2. Colors

```yaml
colors:
  primary: "#081B32"
  secondary: "#2DB780"
  error: "#EB2C50"
  warning: "#F8DC5D"
  success: "#90CB82"
  info: "#78ACE9"

  surface: "#FFFFFF"
  surface-muted: "#F5F7FA"
  surface-subtle: "#E9EEF5"
  border: "#D5DCE5"

  text-primary: "#081B32"
  text-secondary: "#485463"
  text-muted: "#8A94A3"
  text-inverse: "#FFFFFF"
```

## Color Meaning

| Token | Hex | Usage |
|---|---|---|
| Primary | `#081B32` | Core brand color, headings, navigation, primary buttons, key text |
| Secondary | `#2DB780` | Success and positive emphasis |
| Error | `#EB2C50` | Errors, destructive states, critical warnings |
| Warning | `#F8DC5D` | Cautionary states and attention cues |
| Success | `#90CB82` | Success feedback and completed states |
| Info | `#78ACE9` | Informational messages and neutral guidance |
| Surface | `#FFFFFF` | Base background for cards, panels, inputs |
| Surface Muted | `#F5F7FA` | Grouped sections and subtle backgrounds |
| Surface Subtle | `#E9EEF5` | Headers and separators |
| Border | `#D5DCE5` | Inputs, cards, tables, containers |
| Text Primary | `#081B32` | Titles and primary text |
| Text Secondary | `#485463` | Supporting text |
| Text Muted | `#8A94A3` | Helper text and low-emphasis metadata |
| Text Inverse | `#FFFFFF` | Text on dark/primary surfaces |

### Color Rules

- Use primary for core structure and hierarchy.
- Use secondary for positive emphasis.
- Use semantic colors consistently.
- Never rely on color alone to communicate meaning.
- Pair semantic states with icons, labels, or other visual cues.
- Avoid introducing random colors outside the defined palette.

---

# 3. Typography

Typography is one of the strongest signals of the design system.

Use:

- **DM Serif Display** for large display moments and brand-forward headings.
- **Montserrat** for the rest of the interface.

```yaml
typography:
  display-xl:
    fontFamily: "DM Serif Display"
    fontSize: 56px
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: 0em

  heading-xl:
    fontFamily: "Montserrat"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.02em

  heading-lg:
    fontFamily: "Montserrat"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: -0.01em

  heading-md:
    fontFamily: "Montserrat"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.3

  body-lg:
    fontFamily: "Montserrat"
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.6

  body-md:
    fontFamily: "Montserrat"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6

  body-sm:
    fontFamily: "Montserrat"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5

  label-md:
    fontFamily: "Montserrat"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.35

  label-sm:
    fontFamily: "Montserrat"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.25
```

## Typography Hierarchy

- **Display XL** — large page or brand moments
- **Heading XL** — major page titles
- **Heading LG** — section titles
- **Heading MD** — component titles
- **Body LG** — larger readable content
- **Body MD** — primary body text
- **Body SM** — supporting content and dense information
- **Label MD** — controls, navigation, form labels
- **Label SM** — small metadata and helper labels

### Typography Rules

- Keep hierarchy strong and predictable.
- Keep body text calm and readable.
- Avoid mixing too many font families.
- Avoid unnecessary decorative typography.
- Keep labels clear without making them cramped.

---

# 4. Spacing

Use an **8px spacing rhythm**.

```yaml
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
```

## Spacing Rules

- Use consistent spacing between related elements.
- Use larger spacing to separate major sections.
- Keep internal component spacing tighter than page-level spacing.
- Avoid arbitrary spacing values.

---

# 5. Layout

Use a simple, responsive grid with generous vertical spacing.

## Layout Rules

- Use a **12-column responsive grid** on larger screens.
- Keep content centered in a wide container.
- Use consistent gutters.
- Maintain predictable alignment.
- Separate major sections with large vertical spacing.
- Keep related controls close together.
- Make layouts responsive.
- Keep forms and data views easy to scan.

Dense information is acceptable only when the structure remains clear.

---

# 6. Border Radius

```yaml
rounded:
  sm: 4px
  md: 8px
  lg: 16px
  xl: 24px
  full: 9999px
```

## Shape Rules

- **4px** — compact controls such as buttons and inputs
- **8px** — cards, panels, modals, and larger containers
- **16px** — larger surface groupings where appropriate
- **Full rounding** — tags, counters, pills, and filter chips

Shapes should support clarity rather than become the primary visual feature.

---

# 7. Elevation & Depth

Depth should be subtle, not dramatic.

Prefer:

- Soft borders
- Light fills
- Very gentle shadows
- Layered white surfaces

Use stronger elevation only for temporary overlays such as:

- Modals
- Popovers
- Side panels

Cards and table containers should feel grounded rather than heavily floating.

---

# 8. Components

## 8.1 Buttons

### Primary

```yaml
button-primary:
  backgroundColor: "#081B32"
  textColor: "#FFFFFF"
  borderColor: "#081B32"
  typography: "label-md"
  rounded: 4px
  padding: 8px 16px
  height: 40px
```

Use for primary actions.

### Secondary

```yaml
button-secondary:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  typography: "label-md"
  rounded: 4px
  padding: 8px 16px
  height: 40px
```

Use for secondary actions.

### Ghost

```yaml
button-ghost:
  backgroundColor: "transparent"
  textColor: "#081B32"
  borderColor: "transparent"
  typography: "label-md"
  rounded: 4px
  padding: 8px 12px
```

Use for subtle actions and low-emphasis controls.

### Button States

Buttons should provide clear visual states for:

- Hover
- Focus
- Active
- Disabled
- Loading

---

## 8.2 Tags

```yaml
tag-default:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 9999px
  padding: 4px 10px

tag-success:
  backgroundColor: "#90CB82"
  textColor: "#FFFFFF"
  borderColor: "#90CB82"
  rounded: 9999px
  padding: 4px 10px

tag-warning:
  backgroundColor: "#F8DC5D"
  textColor: "#081B32"
  borderColor: "#F8DC5D"
  rounded: 9999px
  padding: 4px 10px

tag-error:
  backgroundColor: "#EB2C50"
  textColor: "#FFFFFF"
  borderColor: "#EB2C50"
  rounded: 9999px
  padding: 4px 10px

tag-neutral:
  backgroundColor: "#F5F7FA"
  textColor: "#485463"
  borderColor: "#D5DCE5"
  rounded: 9999px
  padding: 4px 10px
```

Tags should stay compact and easy to scan.

Support:

- Default
- Removable
- Outline
- Semantic variants

---

## 8.3 Cards

### Outlined Card

```yaml
card-outlined:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 16px
  padding: 24px
```

### Filled Card

```yaml
card-filled:
  backgroundColor: "#F5F7FA"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 16px
  padding: 24px
```

### Elevated Card

```yaml
card-elevated:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 16px
  padding: 24px
  shadow: "0 10px 30px rgba(8, 27, 50, 0.08)"
```

Use cards to group related content and actions.

Keep card content:

- Compact
- Organized
- Clearly titled
- Focused on related information

---

## 8.4 Side Navigation

```yaml
side-navigation:
  backgroundColor: "#081B32"
  textColor: "#FFFFFF"
  activeItemBackgroundColor: "#FFFFFF"
  activeItemTextColor: "#081B32"
  borderColor: "#081B32"
  width: 280px
```

Use:

- Dark vertical navigation
- Simple labels
- Clear spacing
- Strong active-state contrast

The current location should always be obvious.

---

## 8.5 Side Panel

```yaml
side-panel:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 8px
  padding: 24px
  shadow: "0 18px 48px rgba(8, 27, 50, 0.14)"
  width: 560px
```

Use a side panel for contextual information or actions without leaving the current page.

Include:

- Clear header
- Close control
- Relevant content
- Actions at the bottom

---

## 8.6 Tables

```yaml
table:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  headerBackgroundColor: "#E9EEF5"
  rowBackgroundColor: "#FFFFFF"
  rowStripedBackgroundColor: "#F5F7FA"
  typography: "body-sm"
  padding: 12px 16px
```

Table rules:

- Use clear headers.
- Align columns consistently.
- Use row separation.
- Use optional striping for scanability.
- Use status tags when appropriate.
- Avoid overcrowding columns.
- Keep structured content mostly rectangular.

---

## 8.7 Breadcrumbs

```yaml
breadcrumb:
  textColor: "#485463"
  activeTextColor: "#081B32"
  separatorColor: "#8A94A3"
```

Use breadcrumbs only when the hierarchy is meaningful.

Keep the trail:

- Short
- Quiet
- Readable

The current page should be visually distinct.

---

## 8.8 Modal

```yaml
modal:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 8px
  padding: 24px
  shadow: "0 18px 48px rgba(8, 27, 50, 0.18)"
```

Use modals sparingly for:

- Important confirmation
- Interruption
- Decisions
- Short focused forms

A modal should have:

- Concise title
- Clear body
- Obvious primary action
- Obvious secondary action

Do not overload a modal with content.

---

## 8.9 Popover

```yaml
popover:
  backgroundColor: "#081B32"
  textColor: "#FFFFFF"
  rounded: 8px
  padding: 12px 14px
```

Use popovers for contextual information or quick actions.

They should:

- Stay small
- Be easy to dismiss
- Remain anchored to their target
- Avoid blocking the full interface

---

## 8.10 Radio Buttons

```yaml
radio-button:
  selectedColor: "#081B32"
  unselectedColor: "#D5DCE5"
  labelColor: "#081B32"
```

Use for mutually exclusive choices.

Rules:

- Group related choices clearly.
- Keep labels aligned.
- Show selected state with strong contrast.
- Use horizontal layout only for small choice sets.

---

## 8.11 Dropdowns

```yaml
dropdown:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 4px
  padding: 10px 12px
```

Use for single-select and multi-select interactions.

Open menus should remain clean and easy to scan.

For multi-select:

- Display selected values as removable chips.
- Keep the trigger readable.
- Avoid overcrowding the control.

---

## 8.12 Search Field

```yaml
search-field:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 4px
  padding: 10px 12px
```

Use a search field when the context already makes its purpose obvious.

Keep it:

- Compact
- Clear
- Easy to scan
- Consistent with other inputs

---

## 8.13 Filter Chips

```yaml
filter-chip:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 9999px
  padding: 4px 10px
```

Filters should remain lightweight and easy to scan.

Active filters must be:

- Visually distinct
- Easy to identify
- Removable

---

## 8.14 Counter

```yaml
counter:
  backgroundColor: "#081B32"
  textColor: "#FFFFFF"
  rounded: 9999px
  size: 20px
```

Use counters for numeric quantities only.

Keep counters small and compact.

Use formats such as:

- `1`
- `12`
- `99+`

Avoid oversized numeric indicators.

---

## 8.15 Text Field

```yaml
text-field:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 4px
  padding: 10px 12px
```

Use:

- Clear labels
- Consistent borders
- Predictable spacing
- Visible states

Prefixes, icons, and password actions should remain integrated and unobtrusive.

### Error State

```yaml
text-field-error:
  backgroundColor: "#FFFFFF"
  textColor: "#081B32"
  borderColor: "#EB2C50"
  rounded: 4px
  padding: 10px 12px
```

---

# 9. Toast Notifications

Use toast notifications for non-blocking feedback.

## Success

```yaml
toast-success:
  backgroundColor: "#FFFFFF"
  accentColor: "#2DB780"
  textColor: "#081B32"
  borderColor: "#2DB780"
  rounded: 8px
  padding: 12px 16px
```

## Info

```yaml
toast-info:
  backgroundColor: "#FFFFFF"
  accentColor: "#78ACE9"
  textColor: "#081B32"
  borderColor: "#D5DCE5"
  rounded: 8px
  padding: 12px 16px
```

## Warning

```yaml
toast-warning:
  backgroundColor: "#FFFFFF"
  accentColor: "#F8DC5D"
  textColor: "#081B32"
  borderColor: "#F8DC5D"
  rounded: 8px
  padding: 12px 16px
```

## Error

```yaml
toast-error:
  backgroundColor: "#FFFFFF"
  accentColor: "#EB2C50"
  textColor: "#081B32"
  borderColor: "#EB2C50"
  rounded: 8px
  padding: 12px 16px
```

Toast messages should be:

- Temporary
- Compact
- Clear
- Immediately understandable

---

# 10. Warning and Error States

Use explicit semantic cards or banners for:

- Error
- Warning
- Success
- Info

Pair semantic color with:

- Icons
- Labels
- Clear text

Do not communicate important states through color alone.

---

# 11. Grids

Use grid layouts to organize:

- Cards
- Controls
- Content blocks
- Structured sections

Grid rules:

- Keep spacing consistent.
- Align related content.
- Use responsive behavior.
- Collapse cleanly on smaller screens.

---

# 12. Form Patterns

Forms should remain easy to scan.

Use:

- Clear labels
- Consistent input styling
- Predictable vertical spacing
- Logical grouping
- Visible validation
- Clear primary and secondary actions

Do not make forms visually dense without strong grouping.

---

# 13. Data View Patterns

Data-heavy interfaces should prioritize scanability.

Use:

- Clear table headers
- Consistent alignment
- Search
- Filters
- Status tags
- Compact metadata
- Predictable actions

Avoid unnecessary information density.

---

# 14. Do's

- Keep the interface calm, structured, and consistent.
- Use the defined color meanings for state and feedback.
- Keep typography hierarchy strong and predictable.
- Use subtle borders and shadows instead of heavy decoration.
- Keep components compact and readable.
- Use consistent spacing.
- Use semantic states consistently.
- Keep navigation obvious.
- Keep controls visually related across the interface.

---

# 15. Don'ts

- Don't add random colors.
- Don't add random effects.
- Don't add unnecessary font families.
- Don't rely on color alone to communicate status.
- Don't overload cards.
- Don't overload tables.
- Don't make controls look different without a reason.
- Don't break the spacing rhythm with arbitrary values.
- Don't use heavy decoration when hierarchy and spacing can communicate the same thing.

---

# 16. Core Design Tokens

```yaml
version: "alpha"

colors:
  primary: "#081B32"
  secondary: "#2DB780"
  error: "#EB2C50"
  warning: "#F8DC5D"
  success: "#90CB82"
  info: "#78ACE9"
  surface: "#FFFFFF"
  surface-muted: "#F5F7FA"
  surface-subtle: "#E9EEF5"
  border: "#D5DCE5"
  text-primary: "#081B32"
  text-secondary: "#485463"
  text-muted: "#8A94A3"
  text-inverse: "#FFFFFF"

typography:
  display-xl:
    fontFamily: "DM Serif Display"
    fontSize: 56px
    fontWeight: 400
    lineHeight: 1.05
  heading-xl:
    fontFamily: "Montserrat"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
  heading-lg:
    fontFamily: "Montserrat"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.25
  heading-md:
    fontFamily: "Montserrat"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.3
  body-lg:
    fontFamily: "Montserrat"
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.6
  body-md:
    fontFamily: "Montserrat"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: "Montserrat"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  label-md:
    fontFamily: "Montserrat"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.35
  label-sm:
    fontFamily: "Montserrat"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.25

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px

rounded:
  sm: 4px
  md: 8px
  lg: 16px
  xl: 24px
  full: 9999px

layout:
  grid: 12
  spacingRhythm: 8px
```

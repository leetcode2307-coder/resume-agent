# Resume AI Agent — Design System Specification (`DESIGN.md`)

> **Version**: 1.0.0  
> **Platform**: Flutter (Web, Desktop, Mobile)  
> **Aesthetic Profile**: Production Minimalist / Precision SaaS (Linear / Vercel inspired)  
> **Typography Family**: Inter (`google_fonts`)  
> **Target Form Factors**: Responsive Web / Cross-Platform Desktop & Mobile

---

## 1. Design Principles

1. **Precision & Density Over Ornamentation**
   - High information density without visual clutter.
   - Use crisp 1px borders, subtle surface elevations, and meticulous whitespace rather than heavy drop shadows, neon glows, or multi-stop gradients.
2. **Deterministic Information Hierarchy**
   - Critical data (ATS match rates, score gauges, pipeline bottlenecks) must be scannable in under 3 seconds.
   - Structural dividers and cards group related AI agent outputs cleanly.
3. **Living Real-Time Feedback (Streaming First)**
   - Because data streams live via Server-Sent Events (SSE) from LangGraph, loading states are not static spinners. They use calibrated pulse animations, step-indicator glow lines, and progressive component transitions.
4. **Utilitarian Elegance**
   - Styled after modern developer and productivity suites (Linear, GitHub, Vercel). High contrast, functional monochrome base, and purposeful semantic color coding.

---

## 2. Color System & Semantic Tokens

All colors are formulated with accessible WCAG AAA/AA contrast targets. The system adheres to strict semantic tokens mapped to Flutter's `ColorScheme` and custom extensions.

### 2.1 Palette Overview

| Token Name | Light Mode (`HEX`) | Dark Mode (`HEX`) | Semantic Purpose |
| :--- | :--- | :--- | :--- |
| `background` | `#F8FAFC` (Slate 50) | `#080B10` (Obsidian) | Root canvas background |
| `surface` | `#FFFFFF` (White) | `#0F141C` (Dark Charcoal) | Default container / card fill |
| `surface-secondary` | `#F1F5F9` (Slate 100) | `#161C26` (Raised Surface) | Hover states, tab backgrounds, secondary chips |
| `border-subtle` | `#E2E8F0` (Slate 200) | `#1E2634` (Muted Border) | Default card borders, dividers, outlines |
| `border-prominent`| `#CBD5E1` (Slate 300) | `#2E3A4E` (Border Active)| Focused borders, interactive hover lines |
| `text-primary` | `#0F172A` (Slate 900) | `#F8FAFC` (Slate 50) | High-emphasis headings and primary copy |
| `text-secondary` | `#475569` (Slate 600) | `#94A3B8` (Slate 400) | Form labels, descriptions, subheadings |
| `text-tertiary` | `#94A3B8` (Slate 400) | `#64748B` (Slate 500) | Disabled elements, placeholder copy, timestamps |
| `brand-primary` | `#0284C7` (Sky 600) | `#38BDF8` (Sky 400) | Primary actions, pipeline active states |
| `brand-hover` | `#0369A1` (Sky 700) | `#0EA5E9` (Sky 500) | Button hover & active interactions |
| `brand-subtle` | `#E0F2FE` (Sky 100) | `#082F49` (Sky 950) | Primary badges, highlight row backgrounds |
| `success` | `#059669` (Emerald 600) | `#10B981` (Emerald 500)| High ATS match, approved critiques, ready files |
| `success-subtle` | `#ECFDF5` (Emerald 50) | `#064E3B` (Emerald 950)| Success pill backgrounds |
| `warning` | `#D97706` (Amber 600) | `#F59E0B` (Amber 500) | Medium ATS score, items needing user attention |
| `warning-subtle` | `#FFFBEB` (Amber 50) | `#451A03` (Amber 950) | Warning pill backgrounds |
| `error` | `#E11D48` (Rose 600) | `#F43F5E` (Rose 500) | Failed pipeline node, missing keywords, bad grammar |
| `error-subtle` | `#FFF1F2` (Rose 50) | `#4C0519` (Rose 950) | Error alerts, weak phrase highlight boxes |

### 2.2 Flutter `ThemeData` Token Mapping

```dart
// lib/core/theme/color_tokens.dart
import 'package:flutter/material.dart';

class AppColors {
  // Light Canvas
  static const lightBackground = Color(0xFFF8FAFC);
  static const lightSurface = Color(0xFFFFFFFF);
  static const lightSurfaceSecondary = Color(0xFFF1F5F9);
  static const lightBorderSubtle = Color(0xFFE2E8F0);
  static const lightBorderProminent = Color(0xFFCBD5E1);
  static const lightTextPrimary = Color(0xFF0F172A);
  static const lightTextSecondary = Color(0xFF475569);
  static const lightTextTertiary = Color(0xFF94A3B8);

  // Dark Canvas
  static const darkBackground = Color(0xFF080B10);
  static const darkSurface = Color(0xFF0F141C);
  static const darkSurfaceSecondary = Color(0xFF161C26);
  static const darkBorderSubtle = Color(0xFF1E2634);
  static const darkBorderProminent = Color(0xFF2E3A4E);
  static const darkTextPrimary = Color(0xFFF8FAFC);
  static const darkTextSecondary = Color(0xFF94A3B8);
  static const darkTextTertiary = Color(0xFF64748B);

  // Semantics (Adaptive)
  static const brand = Color(0xFF0284C7);
  static const brandDark = Color(0xFF38BDF8);
  static const success = Color(0xFF10B981);
  static const warning = Color(0xFFF59E0B);
  static const error = Color(0xFFF43F5E);
}
```

---

## 3. Typography System

The interface uses **Inter** across all devices for its exceptional legibility at small sizes and high optical fidelity on high-DPI displays.

### 3.1 Type Scale & Specs

| Style Role | Font Size | Weight | Line Height | Letter Spacing | Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `displayLarge` | 32px | Bold (700) | 40px (1.25) | -0.025em | Main metric cards / Auth welcome banner |
| `displayMedium`| 24px | SemiBold (600)| 32px (1.33) | -0.020em | Screen & section headers |
| `headlineSmall`| 18px | SemiBold (600)| 26px (1.44) | -0.015em | Card headers, modal titles |
| `titleMedium` | 15px | Medium (500) | 22px (1.46) | -0.010em | Form section labels, sub-card headings |
| `bodyLarge` | 14px | Regular (400) | 22px (1.57) | 0.000em | Long-form resume rewrites, critique advice |
| `bodyMedium` | 13px | Regular (400) | 20px (1.53) | 0.000em | Standard table copy, descriptions |
| `labelLarge` | 13px | Medium (500) | 18px (1.38) | +0.010em | Button labels, interactive triggers |
| `labelSmall` | 11px | SemiBold (600)| 14px (1.27) | +0.025em | Badge pills, status indicators, tabs |
| `codeSnippet` | 12px | Regular (400) | 18px (1.50) | 0.000em | JSON outputs, keyword token badges |

---

## 4. Spatial System & Elevation

### 4.1 Spacing Grid (8pt System)
- `xxs`: 2px
- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px
- `xxl`: 48px
- `xxxl`: 64px

### 4.2 Radii Tokens
- `radius-none`: 0px
- `radius-sm`: 4px (Buttons, badges, tags)
- `radius-md`: 8px (Form inputs, popovers, nested items)
- `radius-lg`: 12px (Cards, modal containers, pipeline bar)
- `radius-xl`: 16px (PDF Banner, hero modules)
- `radius-full`: 9999px (Circular progress indicators, avatar bubbles)

### 4.3 Border & Shadow System (Elevation)
To maintain the minimal aesthetic, **avoid multi-layered Gaussian drop shadows**. Instead, elevation is expressed via 1px border contrast and ambient micro-shadows:
- **Card Default (Resting)**:
  - Light: `1px solid #E2E8F0`, Shadow: `0 1px 2px rgba(0, 0, 0, 0.04)`
  - Dark: `1px solid #1E2634`, Shadow: `0 1px 3px rgba(0, 0, 0, 0.35)`
- **Card Hover / Active**:
  - Light: `1px solid #CBD5E1`, Shadow: `0 4px 6px -1px rgba(0, 0, 0, 0.06)`
  - Dark: `1px solid #2E3A4E`, Shadow: `0 4px 12px rgba(0, 0, 0, 0.5)`

---

## 5. Component Library Specifications

### 5.1 Sticky App Bar
- **Height**: 60px fixed.
- **Positioning**: Sticky top (`kToolbarHeight` + safe area).
- **Background**: Blur glassmorphism effect:
  - Light: `rgba(255, 255, 255, 0.85)` with `BackdropFilter` sigma `10`
  - Dark: `rgba(8, 11, 16, 0.85)` with `BackdropFilter` sigma `10`
- **Border**: Bottom 1px border (`border-subtle`).
- **Items**:
  - **Left**: Minimal Wordmark + Logo (Inter 600, 16px).
  - **Center**: Current Live Run Status Indicator (e.g., `Idle`, `Analyzing Resume...`, `Complete`).
  - **Right Actions**:
    - `Reset` Text-Icon button.
    - `Theme Toggle` Icon button (Sun/Moon).
    - Supabase `Logout` button (Ghost style).

### 5.2 Workflow Pipeline Indicator
A 4-step horizontal timeline displaying:
1. `Analyzer` $\rightarrow$ 2. `Rewriter` $\rightarrow$ 3. `Critique` $\rightarrow$ 4. `Interview`

- **Node States**:
  - **Pending**: Grey circle ring (`text-tertiary`), muted text.
  - **Active / Streaming**: Sky blue pulsing indicator with spinning micro-loader, bold label.
  - **Completed**: Emerald solid circle with white Checkmark icon (`Icons.check_rounded`), connecting bridge line colored Emerald.
  - **Error / Interrupted**: Rose solid circle with exclamation icon (`Icons.close_rounded`).
- **Connector Line**: 2px thick track connecting each node.

### 5.3 Collapsible Input Form
- **Structure**: Collapsible accordion wrapped in a card container. Defaults open; automatically collapses to a compact 48px summary strip when the LangGraph pipeline is running.
- **Text Inputs**:
  - `Resume Markdown / Text` Area (Min 160px height).
  - `Job Description` Area (Min 160px height).
  - `Collapsible Advanced Fields`: Single-line inputs for Name, Email, LinkedIn, GitHub in a 2-column grid.
- **Input Field Specs**:
  - Surface: `surface-secondary` fill.
  - Border: 1px `border-subtle` transitioning to 1.5px `brand-primary` on focus.
  - Content Padding: 12px horizontal, 12px vertical.
  - Typography: 13px Inter Regular.

### 5.4 AI Results Section

#### A. Analyzer Card
- **Circular Gauge Indicators**:
  - Dual circular arc gauges: **ATS Match Score** (%) and **Job Alignment Score** (%).
  - Stroke thickness: 8px with rounded caps.
  - Gauge Colors: $<50\%$ Error (Rose), $50\text{--}74\%$ Warning (Amber), $\ge 75\%$ Success (Emerald).
- **Skill Chips**:
  - `Matching Skills`: Light green background with dark green border + label.
  - `Missing / Gap Skills`: Soft rose background with rose border + cross/minus prefix.
- **Strengths & Weaknesses**:
  - Clean two-column bullet list with checkmark and warning icons.

#### B. Rewriter Card
- **Interface**: Segmented Tab Bar (`Tailored Bullets` | `Full Resume` | `Cover Letter`).
- **Interaction**:
  - One-click "Copy to Clipboard" floating button with micro-tooltip toast.
  - Diff view toggle highlighting added action verbs and metrics.

#### C. Critique Card
- **Scores**: Rating out of 10 with revision iteration counter badge (`Iteration 2 of 3`).
- **Weak Phrasing Alert Box**:
  - Callout box with rose accent border.
  - Displays strikethrough comparison: `"Responsible for managing bugs"` $\rightarrow$ `"Engineered automated regression suite reducing bug leakage by 34%"`.

#### D. Interview Prep Card
- **Tabs**: `Technical Questions`, `Resume Gaps`, `Strategy & Tips`.
- **Card Format**: Collapsible expansion tiles per question with model STAR responses (Situation, Task, Action, Result) in a subtle nested slate container.

#### E. PDF Export Banner
- **Placement**: Pinned directly beneath the App Bar or docked at the bottom of the dashboard once pipeline status reaches `COMPLETE`.
- **Appearance**: Elevated banner with an Emerald/Sky gradient border, icon of generated document, file size indicator, and a prominent `Download PDF` button.

---

## 6. Motion & Micro-Interactions

| Interaction | Trigger / State | Specification |
| :--- | :--- | :--- |
| **Pipeline Node Pulse** | LangGraph SSE node active | `2000ms` infinite pulse, scale `1.0` to `1.08`, opacity `0.4` to `0.8`, `Curves.easeInOut` |
| **Skeleton Placeholder** | Waiting for SSE event chunk | Shimmer gradient moving left-to-right (`1400ms`, `Curves.linear`) |
| **Text Stream Reveal** | Receiving Markdown token chunk | Opacity fade-in (`150ms`, `Curves.easeOut`) |
| **Accordion Collapse** | "Run Agent" button clicked | Height interpolation (`300ms`, `Curves.easeInOutCubic`) |
| **Card Hover** | Mouse cursor enters card boundary | Border color transition + `2px` translateY (`180ms`, `Curves.easeOut`) |
| **Theme Switch** | Theme toggle button pressed | Seamless cross-fade color transition (`250ms`, `Curves.easeInOut`) |

---

## 7. Responsive Breakpoint Guide

- **Mobile (`< 640px`)**:
  - Single column view.
  - Inputs and results stacked vertically.
  - Pipeline indicator converts to a compact horizontal scrollable bar or step pill.
- **Tablet (`640px - 1024px`)**:
  - Single column with max-width container (`720px`) centered on screen.
- **Desktop (`> 1024px`)**:
  - Split two-column workflow dashboard:
    - **Left column (40% width)**: Collapsible input form & sticky pipeline controls.
    - **Right column (60% width)**: Real-time streaming output stream (Analyzer, Rewriter, Critique, Interview).
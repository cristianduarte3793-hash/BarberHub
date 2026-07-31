---
name: Executive Barber Productivity Suite
colors:
  surface: '#16130b'
  surface-dim: '#16130b'
  surface-bright: '#3d392f'
  surface-container-lowest: '#110e07'
  surface-container-low: '#1f1b13'
  surface-container: '#231f17'
  surface-container-high: '#2d2a21'
  surface-container-highest: '#38342b'
  on-surface: '#eae1d4'
  on-surface-variant: '#d0c5af'
  inverse-surface: '#eae1d4'
  inverse-on-surface: '#343027'
  outline: '#99907c'
  outline-variant: '#4d4635'
  surface-tint: '#e9c349'
  primary: '#f2ca50'
  on-primary: '#3c2f00'
  primary-container: '#d4af37'
  on-primary-container: '#554300'
  inverse-primary: '#735c00'
  secondary: '#c6c6c6'
  on-secondary: '#2f3131'
  secondary-container: '#454747'
  on-secondary-container: '#b5b5b5'
  tertiary: '#bfcdff'
  on-tertiary: '#082b72'
  tertiary-container: '#97b0ff'
  on-tertiary-container: '#254188'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe088'
  primary-fixed-dim: '#e9c349'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#574500'
  secondary-fixed: '#e2e2e2'
  secondary-fixed-dim: '#c6c6c6'
  on-secondary-fixed: '#1a1c1c'
  on-secondary-fixed-variant: '#454747'
  tertiary-fixed: '#dbe1ff'
  tertiary-fixed-dim: '#b4c5ff'
  on-tertiary-fixed: '#00174b'
  on-tertiary-fixed-variant: '#27438a'
  background: '#16130b'
  on-background: '#eae1d4'
  surface-variant: '#38342b'
typography:
  display-lg:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Montserrat
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Montserrat
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Montserrat
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-bold:
    fontFamily: Montserrat
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-md:
    fontFamily: Montserrat
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  display-lg-mobile:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  sidebar_width: 260px
  container_padding: 24px
  gutter: 16px
  stack_sm: 8px
  stack_md: 16px
  stack_lg: 32px
---

## Brand & Style
The design system for the barber role is centered on "Prestige Efficiency." It targets high-end grooming professionals who require a high-density, high-productivity dashboard that doesn't sacrifice the luxury aesthetic of the executive brand. 

The design style is **Corporate Modern with a Dark Mode focus**. It utilizes a deep, monochromatic foundation to allow status colors and gold accents to function as critical wayfinding elements. The interface should feel like a high-performance instrument—precise, expensive, and reliable. All interactions should be snappy, with clear visual feedback that respects the fast-paced environment of a premium barbershop.

## Colors
The palette is anchored by the #121414 matte black surface. Gold (#D4AF37) is used strictly for high-level brand moments, primary actions, and active navigation states.

Functional color is the driver of the barber's dashboard:
- **Green (#28A745):** Signifies readiness and confirmed revenue.
- **Yellow/Orange (#FFC107):** Indicates attention required or pending confirmation.
- **Purple (#6F42C1):** Represents active service time ("In the chair").
- **Red (#DC3545):** Critical alerts or lost appointments.
- **Dark Gray (#6C757D):** Used for completed tasks or blocked time slots to reduce visual noise.

## Typography
Montserrat provides a geometric, modern, and highly legible framework. For this dashboard, we prioritize information density. 

**Heading styles** use heavier weights (600-700) to create clear section breaks in data-heavy views. **Labels** use uppercase styling with slight letter spacing (0.05em) when denoting status or metadata. **Body text** should stay at 14px for general data to allow for more content on-screen, while 16px is reserved for primary user inputs and messages.

## Layout & Spacing
The layout utilizes a **Fixed Sidebar** model for the barber role to ensure navigation is never lost during rapid task-switching. 

- **Sidebar:** 260px width, fixed to the left. Contains the barber's profile, schedule toggle, and performance metrics.
- **Main Content:** A fluid area using a 12-column grid. 
- **Rhythm:** A strict 8px base unit is used. 16px gutters between cards provide enough breathing room to prevent the dark interface from feeling cramped. 
- **Responsive:** On tablet, the sidebar collapses into a narrow icon-only rail (72px). On mobile, the sidebar moves to a bottom navigation bar for thumb-optimized access.

## Elevation & Depth
In this dark-themed design system, depth is achieved through **Tonal Layering** and **Subtle Shadows**:

1.  **Base Layer (#121414):** The canvas.
2.  **Card Layer (#1E2020):** Elevated slightly. It uses a very subtle 1px border (#2C2E2E) to define edges against the black background.
3.  **Shadows:** Shadows are "Deep & Sharp." Use a low-blur, 15% opacity black shadow to lift cards.
4.  **Status Glow:** Active "In Process" elements may use a soft Purple (#6F42C1) outer glow (4px blur) to draw immediate focus to the current client in the chair.

## Shapes
This design system uses **Rounded (Value: 2)** geometry.
- **Cards & Primary Containers:** 0.5rem (8px) corner radius.
- **Buttons & Input Fields:** 0.5rem (8px) corner radius for a cohesive look.
- **Chips/Status Tags:** Fully rounded (pill) to distinguish them from interactive buttons.
- **Avatars:** Circular (50% radius) to contrast against the predominantly rectangular layout.

## Components
### Cards
Appointment and metric cards are the primary interface unit. They feature an 8px radius, #1E2020 background, and a left-accent border (4px width) colored according to the appointment status.

### Buttons
- **Primary:** Gold (#D4AF37) background with black text.
- **Secondary:** Ghost style with #2C2E2E borders and white text.
- **Status Action:** Small icon-only buttons for "Check-in" or "Finish" using the respective status colors.

### Status Chips
Pill-shaped with a low-opacity background of the status color and a high-opacity text color (e.g., Green background at 15% with solid Green text).

### Fixed Sidebar
A dark vertical rail with Gold active-state indicators (a vertical line on the left edge). It houses the "Next Up" quick-view component.

### Input Fields
Darker than the card surface (#161818), with a Gold 1px border appearing only on focus. Labels sit 4px above the input in `label-bold` style.

### Schedule Timeline
A vertical list where the current time is marked by a Gold horizontal line. Appointment blocks are color-coded by service type or status.
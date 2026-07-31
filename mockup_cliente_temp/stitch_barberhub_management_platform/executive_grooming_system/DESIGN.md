---
name: Executive Grooming System
colors:
  surface: '#121414'
  surface-dim: '#121414'
  surface-bright: '#38393a'
  surface-container-lowest: '#0c0f0f'
  surface-container-low: '#1a1c1c'
  surface-container: '#1e2020'
  surface-container-high: '#282a2b'
  surface-container-highest: '#333535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#c4c7c7'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#2f3131'
  outline: '#8e9192'
  outline-variant: '#444748'
  surface-tint: '#c8c6c5'
  primary: '#c8c6c5'
  on-primary: '#313030'
  primary-container: '#121212'
  on-primary-container: '#7e7d7d'
  inverse-primary: '#5f5e5e'
  secondary: '#e9c349'
  on-secondary: '#3c2f00'
  secondary-container: '#af8d11'
  on-secondary-container: '#342800'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#00160c'
  on-tertiary-container: '#008f62'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e5e2e1'
  primary-fixed-dim: '#c8c6c5'
  on-primary-fixed: '#1c1b1b'
  on-primary-fixed-variant: '#474646'
  secondary-fixed: '#ffe088'
  secondary-fixed-dim: '#e9c349'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#121414'
  on-background: '#e2e2e2'
  surface-variant: '#333535'
typography:
  display-lg:
    fontFamily: Montserrat
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-padding: 24px
  gutter: 16px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style
The design system is engineered for a premium, tech-forward barber shop management experience. It targets high-end grooming establishments that value precision, efficiency, and a luxurious customer experience. 

The visual style is a blend of **Corporate Modern** and **High-Contrast Minimalism**. It utilizes a sophisticated dark-mode foundational layer to evoke the classic "barber chair" leather and steel aesthetic, contrasted with sharp, high-end accents that signal professional-grade software. The emotional response is one of reliability, prestige, and surgical precision.

## Colors
This design system utilizes a high-contrast dark palette to establish its premium positioning.

- **Primary (Carbon Black):** Used for the app shell, sidebars, and primary backgrounds. This creates a deep "stage" for the content.
- **Secondary (Elegant Gold):** Reserved for high-value actions, active states, and brand-critical highlights. Use sparingly to maintain its prestige value.
- **Surface & Neutrals:** Light Gray and Pure White are used exclusively for text readability and surface elevation within cards to create "islands" of information.
- **Semantic Colors:** Emerald Green handles "Available" and "Confirmed" statuses, while Soft Red manages "Cancellations" and "Occupied" slots. These maintain high saturation to stand out against the dark backgrounds.

## Typography
The typography strategy pairings high-impact geometric headers with functional, humanist body text. 

**Montserrat** is used for headings to provide a bold, architectural feel. To maintain the premium aesthetic, keep headings in "Title Case" or "Sentence Case," avoiding all-caps except for small labels.

**Inter** is used for all functional UI text, data tables, and body copy. Its high legibility at small sizes is critical for dense scheduling views and inventory management. Label styles should use a slight letter-spacing increase and uppercase styling to differentiate them from interactive body text.

## Layout & Spacing
The layout follows a **Fluid Grid** system within a 12-column framework for desktop and a single-column stack for mobile. 

- **The Sidebar:** Fixed at 280px on desktop, utilizing the #121212 Carbon Black.
- **Main Content:** Padded with 24px-32px margins to allow the UI to breathe. 
- **The Rhythm:** Uses an 8px base unit. Components should be spaced in multiples of 8 (e.g., 16px between cards, 24px between sections).
- **Mobile Adaptation:** On mobile devices, sidebars collapse into a bottom navigation bar or a hamburger menu, and internal card padding reduces to 16px to maximize screen real estate for the booking calendar.

## Elevation & Depth
Depth is conveyed through **Tonal Layering** and **Soft Shadows**. 

Since the base background is #121212, elevation is achieved by lightening the surface color slightly (to #1E1E1E or #2A2A2A) rather than using heavy drop shadows. 
- **Level 1 (Cards):** Subtle 1px border (#333333) with a 4% opacity shadow.
- **Level 2 (Popovers/Modals):** More pronounced shadow with 15% opacity and a slight gold-tinted ambient glow to draw focus.
- **Backdrop:** Use a 60% black overlay with a 4px backdrop blur (glassmorphism) for modals to maintain context of the schedule behind the interaction.

## Shapes
The shape language is sophisticated and approachable. 
- **Standard Radius:** 12px for cards, input fields, and buttons. This strikes a balance between professional precision and modern softness.
- **Large Radius:** 24px for container sections or promotional banners.
- **Full Radius:** Used only for status badges (chips) and avatar frames to provide visual variety against the predominantly rectangular layout.

## Components
- **Buttons:** Primary buttons use the #D4AF37 Gold background with #121212 text for maximum contrast. Secondary buttons should be "Ghost" style with a gold border and text.
- **Input Fields:** Dark backgrounds (#1E1E1E) with a 1px border. On focus, the border transitions to Gold. Labels sit above the field in uppercase Inter.
- **Cards:** Use #FFFFFF for "Customer Profile" or "Detail" cards to pop against the dark UI, or #1E1E1E for "Schedule" cards to stay integrated.
- **Booking Calendar:** Time slots should be clearly demarcated with thin 1px lines. Available slots use a faint green dashed border; occupied slots are solid grey.
- **Status Chips:** Small, pill-shaped elements. "Confirmed" uses a green background with 10% opacity and solid green text to avoid overwhelming the eye.
- **Imagery:** Use high-contrast, desaturated photography of grooming tools and shop interiors to reinforce the "Premium" narrative.
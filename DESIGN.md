# Design System

## Overview

A disciplined market-intelligence interface for a Streamlit workbench.
Light-first, precise, and information-forward.
The product should feel like a serious research desk: structured, sober, and high-signal,
with quiet stewardship present as conviction rather than softness.

This design system should sharpen the existing SLBR Companion dashboard rather than replace it
with a different product language.
It must preserve the operational shell already visible in the application:
a persistent sidebar command rail, fast tab-to-tab orientation, dense metrics,
chart-heavy analysis, settings management, data-quality views, and compact policy callouts.

## Colors

Monochromatic design with a single accent color for emphasis.

- **Primary** (#1A365D): Deep Navy for titles, highlights, key values, and primary actions
- **Secondary** (#718096): Silver Gray for labels, borders, muted text, and secondary elements
- **Accent** (#3182CE): Ocean Blue for single accent emphasis (stop prices, key callouts)
- **Neutral Light** (#F7FAFC): Frost White for card backgrounds and light surfaces
- **Neutral Mid** (#E2E8F0): Silver Gray for input borders and secondary surfaces
- **Text** (#2D3748): Slate for body text
- **Text Dark** (#1A202C): Charcoal for high contrast text (loss values, important numbers)

Dark text should read as charcoal-navy rather than pure black.
Charts should use Primary for the dominant price or score series,
Secondary for supporting lines and outlines, Positive for aligned overlays,
and Tertiary only when a decision-worthy value needs emphasis.

## Typography

- **Headline Font**: Source Serif 4
- **Body Font**: Source Sans 3
- **Label Font**: Source Sans 3

Headlines use semi-bold weight and appear only at high-trust hierarchy points:
page titles, major section headers, and exceptional summary cards.
Most of the working interface should remain sans-serif so charts, filters,
tables, settings panels, and dense metrics stay crisp and legible in Streamlit.

Body text should typically sit in the 14-16px range with regular or medium weight.
Labels should be compact, disciplined, and sparingly uppercase for metric captions,
section metadata, and compact dashboard chrome.
Serif is a trust signal, not a decorative voice.

## Elevation

This system is mostly flat and structured.
Depth should come from tonal surface steps, border contrast, spacing, and density,
not from heavy shadows or floating cards.

Standard cards, tables, filter trays, and settings groups should use thin borders,
subtle tonal contrast, and restrained rounding.
Only exceptional summary surfaces, modal-like overlays, or priority decision cards
may use a very soft shadow, and even then the result should feel grounded and operational.

## Components

- **Sidebar Command Rail**: The sidebar is a persistent operational rail, not a decorative panel. It should feel dense, clear, and decisive, with strong active-state contrast and short labels that support rapid switching between dashboard views.
- **Navigation and Tabs**: Keep navigation utilitarian and scannable. Use tabs only for genuinely related content clusters and avoid relying on many heavy tabs at once. The user should always understand where they are in the workbench.
- **Metric Cards**: Use compact bordered cards with strong numeric hierarchy, small disciplined labels, and minimal ornament. Important values may use Burnished Brass as a small accent, not as a full-surface fill.
- **Analysis Cards**: Core analysis surfaces should read like bordered research panels. Use thin outlines, quiet surface steps, and structured spacing so price action, factors, and commentary can coexist without visual noise.
- **Buttons**: Use restrained rounding with clear contrast. Primary buttons use Deep Ledger Navy fills; secondary buttons use light surfaces with Steel Slate borders; destructive actions use Oxide Red only when necessary.
- **Inputs and Filter Trays**: Inputs should feel orderly and dense. Favor bordered trays, segmented controls, and grouped filters over soft pills or consumer-style chips. Search, ticker selection, overlays, and settings controls should feel precise.
- **Tables and Dataframes**: Tables must feel like analysis instruments. Preserve readability first with quiet row separation, disciplined spacing, and minimal decorative color. Avoid glossy or presentation-only styling.
- **Charts**: Charts should have neutral framing and minimal chrome. Use Primary for the leading series, Secondary for support structure, Positive for aligned or constructive overlays, and Tertiary only for selective emphasis. Charts should remain legible beside overlay toggles, tooltips, and technical indicators.
- **Settings Surfaces**: Settings pages should use organized sections, clear dividers, compact controls, and sober explanatory text. They should support appearance, chart, and environment configuration without losing operational clarity.
- **Stewardship and Policy Callouts**: Policy, alignment, and stewardship surfaces should be compact, authoritative, and integrated into the analytical workflow. They should feel serious and clear, never ornamental or preachy.
- **Bespoke Polish**: Premium polish should come from Streamlit theming plus selective `st.html` and custom components for high-value surfaces. Core controls, data display, and dashboard information flow should remain recognizably Streamlit-native.

## Do's and Don'ts

- Do make every screen feel decisional, with a clear hierarchy, obvious current state, and obvious next action
- Do preserve the current dashboard shell: sidebar visibility, operational status surfaces, settings flows, and the footer/disclaimer layer should remain visible when relevant
- Do use typography, borders, and spacing to create authority before reaching for extra color
- Do keep layouts compatible with Streamlit workbench realities, including shallow column nesting and disciplined use of tabs
- Do let dense metrics, filters, charts, and tables remain the center of the experience
- Do use Burnished Brass rarely so highlighted scores and decisions still feel important
- Don't make the product feel soft, lifestyle-branded, or devotional
- Don't over-round cards, controls, or inputs
- Don't hide working dashboard information behind decorative hero sections or overly spacious marketing layouts
- Don't rely on heavy shadows, glassmorphism, or loud gradients to create hierarchy
- Don't let custom surfaces drift so far that the application stops feeling like one coherent Streamlit product

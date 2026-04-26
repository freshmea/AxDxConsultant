# Day 16 Design System

## Visual Theme & Atmosphere

This deck uses a cinematic AI-lab aesthetic tailored to a hands-on video generation class. The tone should feel technical, current, and commercially relevant rather than academic or decorative. Slides should look like a cross between an advanced media tool dashboard and an executive workshop handout.

The visual language balances dark control-room backgrounds with bright signal colors. Dense concepts are presented through structured cards, process lanes, and comparison blocks so that technical content remains easy to teach live.

## Colour Palette & Roles

| Role | Name | Hex | Usage |
| --- | --- | --- | --- |
| Background | Carbon Night | `0B1020` | Main slide background |
| Surface | Deep Panel | `121A30` | Cards, panels, diagram containers |
| Surface Alt | Blueprint Navy | `162441` | Section headers, emphasis bands |
| Primary | Signal Cyan | `41D9E6` | Key actions, step markers, diagram links |
| Secondary | Aurora Violet | `7C72FF` | Technical emphasis, architecture accents |
| Accent | Flame Coral | `FF6B57` | Warnings, constraints, output highlights |
| Text Primary | Soft White | `F5F7FB` | Titles and main text |
| Text Secondary | Mist Blue | `AAB7D4` | Supporting labels and body copy |
| Border | Slate Line | `2A3657` | Card borders and dividers |
| Success | Neon Mint | `35D49A` | Checklists, validation, readiness |

## Typography

- Heading font: `Aptos Display` or fallback `Malgun Gothic`
- Body font: `Aptos` or fallback `Malgun Gothic`
- Title scale: 26-32pt in PPTX, 44-56px in HTML
- Section labels: 11-12pt in PPTX, 12-13px in HTML with letter spacing
- Body text: 13.5-16pt in PPTX, 18-22px in HTML
- Speaker note box: 10.5-11.5pt in PPTX, 14-15px in HTML

## Component Styles

- Title block: left-aligned, large title with short kicker label above it.
- Content cards: rectangular cards with 12px visual rounding in HTML and clean rectangular PPT blocks with soft borders.
- Metric chips: compact rounded labels for module, 난이도, 실습 여부.
- Diagram panels: dark panels with contrasting lines, numbered nodes, and short captions.
- Footer note: low-height instruction strip titled `강사 포인트`.

## Layout Principles

- Widescreen 16:9 ratio.
- Generous left and right margins.
- Two-zone layout for most slides: explanation block plus visual block.
- Alternate between `content-left / visual-right` and `visual-left / content-right` to avoid repetition.
- Keep each slide to one teaching objective.

## Design System Notes For Generation

- Use a dark background for every slide.
- Use cyan as the main guidance color and coral only for warnings or business impact callouts.
- Prefer cards, flows, timelines, and comparison structures over long bullets.
- Every slide should include a visible teaching cue for the instructor.

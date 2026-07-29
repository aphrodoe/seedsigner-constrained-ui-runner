# Text UI Design Guide

This document outlines the core rendering rules, constraints, and navigation patterns for displaying the SeedSigner UI across constrained display hardware.

## 1. Core Constraints & Hardware Tiers
Displays are categorized into architectural "Tiers" based on their spatial capacity.

For **character LCDs**, the grid is intrinsic to the hardware (e.g., a 20x4 LCD physically has 20 columns and 4 rows).

For **graphical pixel displays** (OLED, E-Paper), the text grid is **dynamically computed** from the physical pixel dimensions and the loaded font's metrics using `src/utils/graphics.py`:
- `cols = pixel_width // average_char_width`
- `rows = pixel_height // font_ascent`

This means the tier assignment is automatic and hardware-agnostic — plugging in a different resolution display requires zero code changes.

| Tier | Example Hardware | Grid | How Derived |
|:-----|:-----------------|:-----|:------------|
| Tier 0 | 16x2 Character LCD | 16 cols × 2 rows | Intrinsic hardware |
| Tier 1 | 20x4 Character LCD, 128x32 OLED | 20×4 or 21×3 | Intrinsic (LCD) or computed (OLED) |
| Tier 2 | 128x64 OLED | ~21 cols × 6 rows | Computed from pixels |
| Tier 3 | 200x200 E-Paper | ~33 cols × 20 rows | Computed from pixels |

Because of these constraints, the UI logic is fundamentally different from a pixel-based TFT screen.

## 2. Rendering Strategies

### 2.1 Tier 0: Block Pagination (16x2 LCD)
With only 2 rows available, we must reserve Row 0 for the screen title and pagination indicator, leaving only Row 1 for content.
Therefore, the 16x2 display uses **Block Pagination**. The user navigates one item at a time, and the entire Row 1 is replaced by the new item.

**Layout:**
```text
┌──────────────────┐
│Settings     [1/4]│  ← Title (Left), Position (Right)
│> Language        │  ← Selected Item
└──────────────────┘
```

### 2.2 Tier 1: Sliding Window (20x4 LCD)
With 4 rows, we can display multiple items simultaneously. Row 0 remains the title row, but Rows 1-3 act as a **Sliding Window** viewport. The cursor remains vertically centered when possible, and the list scrolls around it.

**Layout:**
```text
┌────────────────────┐
│Settings         2/4│  ← Title (Left), Position (Right)
│  Language          │  ← Previous Item
│> Persistent Setti  │  ← Selected Item
│  Camera            │  ← Next Item
└────────────────────┘
```

### 2.3 Graphical Displays: Dynamic Grid Rendering
On graphical pixel displays (OLED, E-Paper), the text grid is computed dynamically from the hardware's pixel resolution. The `TextRenderer` receives the computed `cols` and `rows` and applies the same tier logic as character LCDs — no special cases.

All graphical rendering is delegated to the shared `src/utils/graphics.py` utility, which provides:
- **`compute_text_grid(width, height, font)`**: Derives `cols`, `rows`, and `line_height` from pixel dimensions.
- **`draw_text_line(draw, image, line, y, font, screen_width, fill)`**: Renders a single line with proportional kerning, icon bitmap substitution, and automatic right-alignment of spaced trailing text (e.g., pagination indicators like `3/4`).

This architecture means adding support for a new graphical display requires only a thin hardware driver that calls the shared API. All alignment, icon rendering, and text layout logic is inherited automatically.

Example: A 128x32 OLED with PIL's default font measures `avg_char_width ≈ 5.9px` and `font_ascent = 10px`, yielding a grid of `21 cols × 3 rows` (1 title + 2 items). A 200x200 E-Paper yields `33 cols × 20 rows`.

### 2.4 Vertical Centering for Text-Only Screens
For screens that do not have active button lists (e.g., wallet descriptors, setting confirmations), the text block is automatically vertically centered within the available display rows. This ensures that on larger displays (Tier 2/3), the text is not awkwardly pinned to the top of the screen.

**Layout:**
```text
┌────────────────────────┐
│                        │ ← Auto-padded
│   Multisig 2-of-3      │
│   Native Segwit        │
│                        │ ← Auto-padded
└────────────────────────┘
```


## 3. Advanced Text Rendering

### 3.1 Marquee Animations (Horizontal Scrolling)
To avoid losing critical context to static truncation (`..`), the engine actively utilizes time-based marquee animations driven by a central `marquee_tick`:
*   **Long Titles**: If a title exceeds available columns, it pauses for 5 ticks, smoothly scrolls to the end, pauses for 5 ticks, and repeats.
*   **Selected Items**: Menu items that are currently selected `> ` will dynamically marquee if they exceed the column constraints. Unselected items remain statically truncated to preserve focus.
*   **Splash Screens**: Subtitle/Partner rows are smoothly scrolled across the bottom row.

### 3.2 Flashing Borders (`warning_edges`)
For screens requiring immediate attention (e.g., `dire_warning_animated`), the engine draws `!` characters around word-wrapped text. If the `animated` flag is true, these edge characters will strobe on and off every ~600ms.

## 4. Icon-to-Text Mapping & CGRAM

We map visual states to ASCII/Unicode text equivalents, and where possible, inject custom 5x8 bitmaps into the LCD hardware's CGRAM (Slots 0-7).

| Upstream LVGL Concept | Constrained UI Equivalent | Hardware CGRAM |
| :--- | :--- | :---: |
| `success` (Checkmark) | `✓` | Yes |
| `warning` (Triangle) | `⚠` | Yes |
| `dire_warning` (Hexagon)| `‼` | Yes |
| `error` (Cross)         | `✕` | Yes |
| Main Menu (Scan)        | `▦` | Yes |
| Main Menu (Seeds)       | `⚿` | Yes |
| Main Menu (Tools)       | `⚒` | Yes |
| Main Menu (Settings)    | `⚙` | Yes |
| Derivation Branch       | `⎇` | ASCII Fallback (`*`) |
| Fingerprint             | `@` | Native ASCII |
| Bitcoin                 | `₿` | ASCII Fallback (`B`) |
| Radio Button (Filled)   | `●` | ASCII Fallback (`o`) |
| Keyboard Mode           | `⌨` | ASCII Fallback (`K`) |
| Edit                    | `✎` | ASCII Fallback (`E`) |
| Alternate Cross         | `✗` | ASCII Fallback (`x`) |
| Info                    | `ℹ` | ASCII Fallback (`i`) |

## 5. Keyboard Navigation & Entry

For screens like `keyboard_screen` (Dice Roll, Coin Flip, BIP85, Derivation), the UI adapts based on the display tier.

### 5.1 1D Carousel (Tier 0 & Tier 1)
On smaller displays, keyboards rely on a 1D horizontal array (a sliding list of characters).
*   **Dynamic Entropy Tracking**: If a target entropy length is set (e.g., 50 for dice), the engine automatically updates the title dynamically (e.g., `Dice Roll 14/50`).
*   **Cursor Mapping**: The `entered_text` is formatted with brackets to indicate focus, e.g., `1234[5]`.

**Example (16x2 Keyboard):**
```text
┌──────────────────┐
│Dice Roll 5/50    │
│1234[5]           │  ← Brackets indicate cursor
└──────────────────┘
```

### 5.2 2D Spatial Grids (Tier 2 & Tier 3 - Planned)
For larger matrix displays, the 1D carousel is inefficient. Future implementation will map the upstream `KeyboardScreen`'s `cols` and `rows` values to render a fully 2D interactive grid (e.g., 3x5 layout for BIP-39 word entry). This requires upgrading the layout engine to use a 2D `ScreenBuffer` coordinate system (`[X, Y]`).

### 5.3 The "Back" Button Constraint
Because text displays compress 2D spatial layouts into 1D loops, upstream LVGL's top-left `<` button is difficult to reach via the D-Pad. To deal with this on a global scale:
1. **Keyboard Screens**: We append `[BACK]` as an explicit item alongside `[DEL]` and `[OK]` within the character carousel.
2. **Hardware Escape**: For immediate top-level escapes, it is recommended to bind one of the dedicated physical side buttons (e.g., Key3) exclusively to "Back/Cancel".

## 6. PSBT Flow Validation

Rendering complex Bitcoin transaction data (PSBTs) requires special layout handling to ensure maximum safety and legibility on small screens.

### 6.1 Transaction Math Wraps
Hardware constraints must never lead to loss of financial data. Instead of truncating large inputs/outputs, the math renderer dynamically evaluates available screen real estate. If the label (e.g., `recipients`) and the transaction amount cannot fit on a single line, the renderer automatically wraps the amount to the next row and right-aligns it, guaranteeing full precision for all numbers.

### 6.2 Visual Address Chunking
To aid in the manual verification of complex addresses, the renderer attempts to recreate the upstream SeedSigner UX by isolating distinct visual chunks. Bech32 addresses are analyzed, and their most critical segments (the prefix, first 8 characters, and last 7 characters) are wrapped in `[ ]` brackets and padded with spaces. This guarantees that `_word_wrap` breaks the address exactly at the optimal boundaries, allowing for quick and accurate human verification.

### 6.3 OP_RETURN Raw Data
If a transaction output contains an OP_RETURN script, the screen must display the raw hex data before the user approves it. On constrained displays, this hex string is wrapped tightly into a continuous block above the navigation buttons, ensuring maximum data visibility without clipping.

### 6.4 Flow Diagrams
When displaying the PSBT Overview, constrained displays lack the graphical capabilities to draw vectors. Instead, the UI dynamically generates an ASCII art representation of the transaction flow, correctly scaling the graphical margins based on the count of inputs and outputs. An animated marquee (e.g. `--->`) connects the inputs to the outputs to simulate flow over time.

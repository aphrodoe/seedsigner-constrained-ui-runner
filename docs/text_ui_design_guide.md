# Text UI Design Guide

This document outlines the core rendering rules, constraints, and navigation patterns for displaying the SeedSigner UI on character LCDs.

## 1. Core Constraints
Character LCDs cannot draw pixels. They rely on fixed-width character grids.
*   **16x2 LCD**: 16 columns, 2 rows. Highly constrained.
*   **20x4 LCD**: 20 columns, 4 rows. Standard constrained.

Because of these constraints, the UI logic is fundamentally different from a pixel-based OLED or TFT screen.

## 2. Rendering Strategies

### 2.1 Block Pagination (16x2 LCD)
With only 2 rows available, we must reserve Row 0 for the screen title and pagination indicator, leaving only Row 1 for content.
Therefore, the 16x2 display uses **Block Pagination**. The user navigates one item at a time, and the entire Row 1 is replaced by the new item.

**Layout:**
```text
┌──────────────────┐
│Settings     [1/4]│  ← Title (Left), Position (Right)
│> Language        │  ← Selected Item
└──────────────────┘
```

### 2.2 Sliding Window (20x4 LCD)
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

| Upstream LVGL Concept | Constrained UI Equivalent | CGRAM Supported |
| :--- | :--- | :---: |
| `success` (Checkmark) | `✓` | Yes |
| `warning` (Triangle) | `⚠` | Yes |
| `dire_warning` (Hexagon)| `‼` | Yes |
| `error` (Cross)         | `✕` | Yes |
| Main Menu (Scan)        | `▦` | Yes |
| Main Menu (Seeds)       | `⚿` | Yes |
| Main Menu (Tools)       | `⚒` | Yes |
| Main Menu (Settings)    | `⚙` | Yes |

## 5. Keyboard Navigation & Entry

For screens like `KeyboardScreen` and synthetic entry screens (Dice Roll, Coin Flip, BIP85), the UI relies on 1D horizontal arrays.

*   **Dynamic Entropy Tracking**: If a target entropy length is set (e.g., 50 for dice), the engine automatically updates the title dynamically (e.g., `Dice Roll 14/50`).
*   **Cursor Mapping**: The `entered_text` is formatted with brackets to indicate focus, e.g., `1234[5]`.

**Example (16x2 Keyboard):**
```text
┌──────────────────┐
│Dice Roll 5/50    │
│1234[5]           │  ← Brackets indicate cursor
└──────────────────┘
```

### 5.1 The "Back" Button Constraint
Because text displays compress 2D spatial layouts into 1D loops, upstream LVGL's top-left `<` button is difficult to reach via the D-Pad. To deal with this on a global scale:
1. **Keyboard Screens**: We append `[BACK]` as an explicit item alongside `[DEL]` and `[OK]` within the character carousel.
2. **Hardware Escape**: For immediate top-level escapes, it is recommended to bind one of the dedicated physical side buttons (e.g., Key3) exclusively to "Back/Cancel".

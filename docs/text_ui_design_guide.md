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

## 3. Truncation Strategy

When a line of text exceeds the column width of the display, it is truncated with a two-dot suffix (`..`).
The truncation logic prioritizes right-aligned content (like pagination indicators) over left-aligned content (like titles).

*   **Example (16x2)**: `Persistent Settings` + `[2/4]` → `Persistent S.. [2/4]`
*   **Example (20x4)**: `BIP85 Child Index Selection` → `BIP85 Child Index..`

## 4. Icon-to-Text Mapping

Because we cannot render SVG icons or PNGs, we map visual states to ASCII/Unicode text equivalents. This is heavily used in the `LargeIconStatusScreen`.

| Upstream LVGL Concept | Constrained UI Equivalent |
| :--- | :--- |
| `success` (Green Checkmark) | `[ ✓ ]` |
| `warning` (Yellow Triangle) | `[ ⚠ ]` |
| `dire_warning` (Red Hexagon)| `[ ‼ ]` |
| `error` (Red Cross)         | `[ ✕ ]` |
| Top-nav Back Button         | `[<]` (Prefix on title) |
| Scrollbar                   | Not rendered (implied by position text) |

## 5. Keyboard Navigation

For screens like `KeyboardScreen` and `SeedAddPassphraseScreen`, the UI renders a localized cursor over the active character or mode.

*   **Row 0**: Top Navigation / Title
*   **Row 1**: The currently entered text (truncated from the left if it overflows, ensuring the cursor remains visible).
*   **Row 2-3 (20x4 only)**: The current keyboard mode (e.g., `[abc/ABC/123]`) and the active character selection.

**Example (16x2 Keyboard):**
```text
┌──────────────────┐
│BIP-39 Passphrase │
│satosh_           │  ← Blinking underscore cursor
└──────────────────┘
```

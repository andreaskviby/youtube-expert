# YouTube Thumbnail Style Guide
## Andreas & Linda's Channel

Based on research from top-performing YouTube channels and CTR optimization studies.

---

## Technical Specifications

| Property | Value |
|----------|-------|
| **Resolution** | 1280 x 720 pixels |
| **Aspect Ratio** | 16:9 |
| **File Size** | Under 2MB |
| **Format** | PNG (preferred) or JPG |

---

## Safe Zones (CRITICAL)

```
┌────────────────────────────────────────────────────────────┐
│ ← 102px →                                    ← 102px →     │
│    ┌──────────────────────────────────────────────┐        │
│    │                                              │   72px │
│    │         ★ SAFE ZONE FOR TEXT ★              │   ↑    │
│    │                                              │        │
│    │    Place all important text and faces       │        │
│    │    within this central area                 │        │
│    │                                              │        │
│    │                                              │   ↓    │
│    └──────────────────────────────────────────────┘   72px │
│                                          ⛔ TIMESTAMP      │
│                                             OVERLAY        │
└────────────────────────────────────────────────────────────┘
```

### Margin Rules
- **Horizontal**: 8% margin = 102 pixels from left/right edges
- **Vertical**: 10% margin = 72 pixels from top/bottom edges
- **Bottom-right corner**: NEVER place text here (YouTube timestamp overlay)
- **Central safe zone**: 1076 x 576 pixels

---

## Text Style Rules

### Title Text
| Property | Standard |
|----------|----------|
| **Position** | Top-left (87% of top thumbnails use this) |
| **Max words** | 3-5 words |
| **Font family** | Bold sans-serif (Impact, Bebas Neue, Anton, Montserrat Black) |
| **Font weight** | 700 or heavier |
| **Coverage** | 20-30% of thumbnail area |
| **Outline** | 4-6px black or contrasting color |
| **Shadow** | Optional drop shadow for depth |

### Text Colors (by content type)
| Content Type | Primary Color | Outline |
|--------------|---------------|---------|
| Action/Drama | RED (#FF0000) or ORANGE (#FF6600) | Black |
| Educational | BLUE (#0066FF) | White |
| Celebration | GOLD (#FFD700) | Black |
| Universal/Accent | YELLOW (#FFFF00) | Black |
| Clean/Minimal | WHITE (#FFFFFF) | Black |

### Episode Number Badge
| Property | Standard |
|----------|----------|
| **Position** | Top-right corner (inside safe zone) |
| **Shape** | Circle or rounded rectangle |
| **Size** | 80-100px diameter |
| **Background** | Solid color matching theme (red, blue, gold) |
| **Text** | White "#XX" format |
| **Font size** | 32-40px bold |
| **Margin from edge** | 20-30px from corner |

---

## Composition Rules

### The Rule of Thirds
```
┌─────────┬─────────┬─────────┐
│         │         │         │
│   👤    │         │  #XX    │
│  FACE   │  TEXT   │ BADGE   │
│         │ AREA    │         │
├─────────┼─────────┼─────────┤
│         │         │         │
│         │         │         │
│         │         │         │
├─────────┼─────────┼─────────┤
│         │         │         │
│         │         │  ⛔     │
│         │         │         │
└─────────┴─────────┴─────────┘
```

### Face Placement
- **Position**: Left third or center
- **Size**: Face should be 30-50% of thumbnail height
- **Expression**: Clear, exaggerated emotion (surprise, joy, concern)
- **Eyes**: Natural, not over-processed (AVOID AI eye enhancement)
- **Lighting**: Well-lit, no harsh shadows on face

### Background
- **Source**: Actual frame from the episode (not AI-generated)
- **Treatment**: Slight blur or darkening to make subjects pop
- **Contrast**: Background should not compete with foreground

---

## Color Psychology

| Color | Emotion | Use For |
|-------|---------|---------|
| RED | Urgency, excitement, danger | Disasters, dramatic reveals, warnings |
| YELLOW | Energy, happiness, attention | Celebrations, discoveries, tips |
| BLUE | Trust, calm, professional | Educational, travel, informative |
| ORANGE | Adventure, warmth, enthusiasm | Exploration, food, activities |
| GREEN | Nature, growth, freshness | Cooking, gardens, olive oil |
| GOLD | Premium, special, celebration | Milestones, secrets, luxury |

---

## Template Layouts

### Layout A: Classic Left-Face
```
┌────────────────────────────────────────┐
│ BOLD TITLE TEXT          [#33]         │
│ WITH OUTLINE                           │
│                                        │
│    👤👤                                │
│   FACES                 [BACKGROUND]   │
│   HERE                                 │
│                                        │
└────────────────────────────────────────┘
```

### Layout B: Center Focus
```
┌────────────────────────────────────────┐
│ [#33]                                  │
│                                        │
│          BOLD TITLE TEXT               │
│            👤  👤                      │
│           FACES HERE                   │
│                                        │
│                                        │
└────────────────────────────────────────┘
```

### Layout C: Split Drama
```
┌────────────────────────────────────────┐
│   DRAMATIC         [#28]               │
│     TEXT                               │
│  ─────────────────────────             │
│    👤  │  👤                           │
│  LEFT  │  RIGHT                        │
│  SCENE │  SCENE                        │
│                                        │
└────────────────────────────────────────┘
```

---

## Checklist Before Publishing

- [ ] Resolution is exactly 1280 x 720
- [ ] File size under 2MB
- [ ] Text is within safe zones (not cut off)
- [ ] No text in bottom-right corner
- [ ] Episode number badge is consistent
- [ ] Faces are natural (no AI artifacts on eyes)
- [ ] Text is readable at phone size (test at 160x90 px)
- [ ] Background is from actual episode
- [ ] Maximum 5 words in title
- [ ] Colors match content emotion

---

## File Naming Convention

```
thumbnail_[episode#]_[short-title].png

Examples:
thumbnail_33_church_surprise.png
thumbnail_35_mountain_climb.png
thumbnail_28_disaster.png
```

---

## Sources

- [YouTube Thumbnail Safe Zone Guide](https://www.thumix.com/blog/youtube-thumbnail-safe-zone)
- [YouTube Thumbnail Best Practices 2025](https://ampifire.com/blog/best-youtube-thumbnail-guide-examples-best-practices-2025-for-high-ctr/)
- [Thumbnail Design Principles 2026](https://www.thumbmagic.co/blog/thumbnail-design-principles)
- [YouTube Official Thumbnail Tips](https://support.google.com/youtube/answer/12340300)

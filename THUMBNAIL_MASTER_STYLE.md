# Master Thumbnail Style Guide
## Andreas & Linda's YouTube Channel

**Reference thumbnail:** `ep33_stylized.png`

---

## THE WINNING STYLE

### Visual Style
- **Semi-stylized / Digital painting look**
- NOT full cartoon, NOT pure photo
- Looks like a premium digital illustration
- Painterly quality while keeping faces recognizable
- Warm, golden lighting with magical atmosphere

### CRITICAL: Face & Body Preservation
- **NEVER make faces look heavier or rounder** than in source photo
- **NEVER make people look older** than they are (Linda is 51, Andreas is mid-50s)
- **Preserve exact facial structure** - cheekbones, jawline, face shape
- **Keep skin smooth and youthful** - no added wrinkles or aging
- **Maintain accurate body proportions** - no weight changes
- The stylization should ONLY affect artistic rendering, NOT physical features

### Composition
- **Subjects:** Left side of frame (approximately 40-50% of width)
- **Background:** Episode-relevant scene on right side (60-50%)
- **Aspect ratio:** 16:9 (1280x720 or 1536x1024)

### Text Elements

#### Main Title
- **Position:** TOP of image, spanning width
- **Style:** Bold, thick, impactful font
- **Color:** White/cream with strong black outline
- **Size:** LARGE (readable at phone thumbnail size)
- **Shadow:** Subtle 3D drop shadow

#### Episode Badge
- **Position:** TOP-RIGHT corner
- **Style:** Red circular badge
- **Text:** White "#XX" format
- **Size:** Approximately 80-100px
- **Margins:** At least 50px from edges

#### Optional Secondary Text
- Can include additional context text in a box
- Example: "WOW! LOOK WE FOUND"
- Position: Below or beside subjects
- Style: Dark background box with light text

---

## WORKFLOW TO RECREATE

### RECOMMENDED: Face-Safe Method (create_thumbnail_v4.py)

This method guarantees 100% face preservation by:
1. Stylizing ONLY the background with AI
2. Compositing the UNTOUCHED original photo on top
3. Adding text with PIL (not AI)

```bash
python create_thumbnail_v4.py --episode 36 --title "IS THIS A GOOD IDEA?" \
    --photo IMG_4665.png --background episode_frames/ep36_frame.png
```

### Step 1: Stylize Background Only
- AI stylizes the kitchen/scene WITHOUT touching the subjects
- Preserves any background people (e.g., Andreas cooking)

### Step 2: Extract Subjects
- rembg removes background from source photo
- Faces remain 100% untouched

### Step 3: Composite with Blending
- Subtle warm color grading to match scene
- Soft edge blur for natural transition
- Gradient fade on right edge

### Step 4: Add Text with PIL
- Impact font, 100px size
- 8px black outline
- Centered, avoiding badge area

### CRITICAL RULES:
- NEVER let AI modify Linda or Andreas's faces
- Linda is 51 - keep her looking natural (not older, not heavier, not thinner)
- Andreas is mid-50s - preserve his actual appearance
- If faces look wrong, use the face-safe method

---

## SOURCE FILES

### Subject Photos (SOURCES folder)
- **IMG_4665.png** - Playful/surprised expressions (good for discovery stories)
- **IMG_5857.png** - Celebration with wine glasses
- **IMG_4614.png** - Mountain/outdoor setting
- Use compressed versions from `SOURCES_compressed/` for faster processing

### Background Sources
- Download current thumbnail: `yt-dlp --write-thumbnail --skip-download -o "episode_frames/[name]" "[youtube_url]"`
- Or extract frame: `ffmpeg -ss [timestamp] -i "[video]" -vframes 1 [output].png`

---

## EXAMPLE PROMPTS BY EPISODE TYPE

### Discovery/Secret Episodes
```
"SECRET SPOT" / "HIDDEN GEM" / "WE FOUND THIS"
Warm golden/turquoise colors, magical atmosphere
```

### Food/Cooking Episodes
```
"HE JUST WALKED IN" / "NONNA'S SECRETS"
Warm kitchen colors, cozy atmosphere
```

### Adventure/Travel Episodes
```
"SPEECHLESS" / "WE MADE IT"
Dramatic landscapes, epic lighting
```

### Celebration Episodes
```
"25K!" / "THANK YOU"
Confetti, party vibes, golden colors
```

---

## TECHNICAL SPECS

| Property | Value |
|----------|-------|
| Resolution | 1280 x 720 px (or 1536 x 1024) |
| Aspect Ratio | 16:9 |
| File Format | PNG |
| Max File Size | 2 MB |
| Color Profile | sRGB |

---

## API SETTINGS

```python
response = client.images.edit(
    model="gpt-image-1",
    image=base_composite,
    prompt=stylization_prompt,
    size="1536x1024"
)
```

---

## QUALITY CHECKLIST

- [ ] Semi-stylized look (not full cartoon, not pure photo)
- [ ] Faces recognizable as Andreas & Linda
- [ ] **Faces NOT made heavier or rounder** than source photo
- [ ] **People NOT made to look older** - preserve youthful appearance
- [ ] Title text fully visible with margins
- [ ] Episode badge fully visible
- [ ] Background tells the episode story
- [ ] Warm, inviting color palette
- [ ] Readable at phone thumbnail size
- [ ] File under 2MB

---

*Created: June 2025*
*Reference: ep33_stylized.png*

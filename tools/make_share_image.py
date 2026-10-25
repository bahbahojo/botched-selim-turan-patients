"""Build the 1200x630 link-preview image (Open Graph / Twitter card) for botchedbyselimturan.com.

Social apps (WhatsApp, Reddit, Facebook, X, iMessage) show this image when someone shares the link.
Layout: Dr. Turan's public profile photo on the left; the title, two evidence photos and his threat on the right.

Run from the repo root (needs Pillow):  python tools/make_share_image.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parent.parent
IMAGES = REPO / "images"
OUT = IMAGES / "share-card.jpg"
FONTS = Path("/System/Library/Fonts/Supplemental")

WIDTH, HEIGHT = 1200, 630
BACKGROUND = (26, 37, 47)  # the site's dark navy
RED = (197, 48, 48)
PINK = (246, 165, 165)
WHITE = (255, 255, 255)
GREY = (203, 213, 224)

# (file, vertical focus 0=top 0.5=centre) for the photo thumbnails; a quote panel follows them.
EVIDENCE: Tuple[Tuple[str, float], ...] = (
    ("image_page14_0.webp", 0.5),  # Patient 2: reopened stitches
    ("sh_1.webp", 0.0),            # his messages to a female patient
)

# His message to the site's author, shown as large text because a screenshot is unreadable at preview size.
QUOTE_LINES: Tuple[str, ...] = ("\u201cgive small", "amount of", "money any", "person he can", "do so many", "bad things\u201d")

# Regions blurred before use, as (file, (left, top, right, bottom)) in source pixels.
# sh_1 contains a phone number in one of his messages; keep it out of every link preview.
REDACT: Tuple[Tuple[str, Tuple[int, int, int, int]], ...] = (
    ("sh_1.webp", (85, 540, 330, 598)),
)


def load(name: str) -> Image.Image:
    """Open an image from images/ as RGB, blurring any REDACT regions listed for it."""
    img = Image.open(IMAGES / name).convert("RGB")
    for redact_name, box in REDACT:
        if redact_name == name:
            img.paste(img.crop(box).filter(ImageFilter.GaussianBlur(14)), box[:2])
    return img


def cover(img: Image.Image, size: Tuple[int, int], focus_y: float = 0.5) -> Image.Image:
    """Scale and crop `img` to fill `size` exactly (like CSS object-fit: cover).

    focus_y picks which part survives a vertical crop: 0 keeps the top, 0.5 the centre.
    """
    target_w, target_h = size
    scale = max(target_w / img.width, target_h / img.height)
    resized = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left = (resized.width - target_w) // 2
    top = round((resized.height - target_h) * focus_y)
    return resized.crop((left, top, left + target_w, top + target_h))


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a system font; fails fast if it's missing so a bad image is never written."""
    return ImageFont.truetype(str(FONTS / name), size)


def build() -> Path:
    """Compose the share image and save it as a JPEG. Returns the output path."""
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    # Left: his public profile photo, with a red divider.
    portrait_w = 360
    portrait = load("image_page1_0.webp")
    canvas.paste(cover(portrait, (portrait_w, HEIGHT), 0.2), (0, 0))
    draw.rectangle((portrait_w, 0, portrait_w + 8, HEIGHT), fill=RED)

    # Right: title, subtitle, three evidence thumbnails, footer.
    x = portrait_w + 48
    right_w = WIDTH - x - 40
    draw.text((x, 34), "Dr. Selim Turan's", font=font("Georgia Bold.ttf", 58), fill=WHITE)
    draw.text((x, 100), "Botched Patients", font=font("Georgia Bold.ttf", 58), fill=WHITE)
    draw.text((x, 178), "Things You Don't See on Instagram", font=font("Georgia Italic.ttf", 30), fill=PINK)

    gap = 16
    panels = len(EVIDENCE) + 1  # photos plus the quote panel
    thumb_w = (right_w - gap * (panels - 1)) // panels
    thumb_h = 280
    top = 240
    for i, (name, focus_y) in enumerate(EVIDENCE):
        thumb = cover(load(name), (thumb_w, thumb_h), focus_y)
        tx = x + i * (thumb_w + gap)
        canvas.paste(thumb, (tx, top))
        draw.rectangle((tx, top, tx + thumb_w - 1, top + 5), fill=RED)  # red top edge, like the site's cards

    # Quote panel: a slightly lighter box with the threat in large italic text.
    qx = x + len(EVIDENCE) * (thumb_w + gap)
    draw.rectangle((qx, top, qx + thumb_w - 1, top + thumb_h - 1), fill=(44, 62, 80))
    draw.rectangle((qx, top, qx + thumb_w - 1, top + 5), fill=RED)
    quote_font = font("Georgia Italic.ttf", 30)
    line_h = 38
    qy = top + (thumb_h - line_h * len(QUOTE_LINES)) // 2 + 4
    for j, line in enumerate(QUOTE_LINES):
        draw.text((qx + 18, qy + j * line_h), line, font=quote_font, fill=WHITE)

    draw.text((x, top + thumb_h + 22), "20 patients · photos · his messages · threats",
              font=font("Georgia Bold.ttf", 24), fill=GREY)
    draw.text((x, top + thumb_h + 56), "botchedbyselimturan.com", font=font("Georgia.ttf", 22), fill=PINK)

    canvas.save(OUT, "JPEG", quality=85, optimize=True, progressive=True)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path.relative_to(REPO)} ({path.stat().st_size // 1024} KB)")

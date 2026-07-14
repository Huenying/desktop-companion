#!/usr/bin/env python3
"""Extract character from confirmed.jpeg (dark background) → character.png with transparency."""

from PIL import Image
import numpy as np
import os

SRC = "confirmed.jpeg"
DST = "character.png"

print(f"Loading {SRC}...")
img = Image.open(SRC).convert("RGBA")
w, h = img.size
pixels = np.array(img)

# Background is pure black (0,0,0) — confirmed by analysis
# Strategy: for each pixel, compute brightness. Near-black = transparent.

# Convert RGB to grayscale brightness (perceived luminance)
r, g, b = pixels[:,:,0].astype(float), pixels[:,:,1].astype(float), pixels[:,:,2].astype(float)
brightness = 0.299 * r + 0.587 * g + 0.114 * b

# Also compute distance from pure black
dist_from_black = np.sqrt(r**2 + g**2 + b**2)

# Create alpha mask: smooth transition
# If brightness < 15 → fully transparent (background noise)
# If brightness > 35 → fully opaque (character)
# Between → smooth gradient (anti-aliased edge)

alpha = np.clip((brightness - 15) / 20.0 * 255, 0, 255).astype(np.uint8)

# Apply the alpha channel
pixels[:,:,3] = alpha

# Find bounding box of non-transparent content
rows = np.any(pixels[:,:,3] > 10, axis=1)
cols = np.any(pixels[:,:,3] > 10, axis=0)
if rows.any() and cols.any():
    y0, y1 = np.where(rows)[0][[0, -1]]
    x0, x1 = np.where(cols)[0][[0, -1]]
    # Add a small padding (10px)
    pad = 10
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(w - 1, x1 + pad)
    y1 = min(h - 1, y1 + pad)
    pixels = pixels[y0:y1+1, x0:x1+1]
    print(f"Cropped to {pixels.shape[1]}x{pixels.shape[0]} (was {w}x{h})")

# Save
result = Image.fromarray(pixels, "RGBA")
result.save(DST, "PNG")
print(f"Saved -> {DST} ({result.size[0]}x{result.size[1]})")
print("Done!")

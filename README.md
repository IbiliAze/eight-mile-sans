# Eight Mile Sans

Brand typeface for Eight Mile Services Ltd. Version 1.000, weights 100–900.

Eight Mile Sans is a modified version of [Outfit](https://github.com/Outfitio/Outfit-Fonts) by Rodrigo Fuenzalida, licensed under the SIL Open Font License 1.1 (see `OFL.txt`). The fonts stay under the same licence.

## What changed from Outfit

- **Taller x-height (+6%).** Lowercase is taller, ascenders unchanged, dots and accents lifted to match. This gives it a friendlier, more open UI feel, in the spirit of Google Sans.
- **Wider lowercase (+3.5%)** so the round letters stay round at the new height.
- **Weight compensation.** Lowercase strokes are pulled back about 5%, so they don't come out heavier than the capitals after the stretch.
- **Looser spacing.** 7 units are added to every side bearing, for better readability at small sizes.
- **Azerbaijani support.** Adds ə (U+0259) and Ə (U+018F).
- **Outfit's own wordmark ligatures removed.** Typing "outfit" no longer swaps in a logo ligature.

The other OpenType features are unchanged: `ss01` (alternate e, g, k, m, n, t, 1, &), `tnum`, `frac`, `dlig` and `liga`.

## Files

- `variable/EightMileSans[wght].ttf`: one file covering all weights (desktop or app).
- `ttf/`: nine static weights, Thin to Black (desktop install).
- `webfonts/`: WOFF2 versions for the web.
- `source/`: the Glyphs source and the script that derives it from Outfit, for refining later in Glyphs or Glyphs Mini.

## Web usage

```css
@font-face {
  font-family: "Eight Mile Sans";
  src: url("/fonts/EightMileSans[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}

body { font-family: "Eight Mile Sans", system-ui, sans-serif; }
```

## Rebuilding

```sh
pip install fontmake glyphsLib
python3 source/make_ems.py path/to/Outfit.glyphs source/EightMileSans.glyphs
fontmake -g source/EightMileSans.glyphs -o variable --filter DecomposeTransformedComponentsFilter
```

## Known first-pass limits

- The capital Ə is generated from the lowercase e and should get a hand-drawn pass.
- Kerning is inherited from Outfit and hasn't been retuned for the new spacing.
- No italics.

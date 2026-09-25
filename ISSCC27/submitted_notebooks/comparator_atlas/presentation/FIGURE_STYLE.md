# Figure style

The final figures follow the IEEE Author Center's graphics recommendations
for size, legibility, vector output and accessible use of color:

- [Graphics and accessibility](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/)
- [Resolution and physical dimensions](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/resolution-and-size/)
- [Formats and embedded fonts](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-graphics-for-your-article/file-formatting/)

## Working profile

| Item | Choice |
| --- | --- |
| Final two-column width | 7.16 in / approximately 182 mm |
| Text at that physical size | 9–9.5 pt |
| Font | Arial when already installed; Liberation Sans or bundled DejaVu Sans as a free fallback |
| Axes and ticks | 0.7 pt |
| Main figure master | PDF, with embedded fonts and vector geometry |
| Editable/web companion | SVG; not claimed as an IEEE manuscript-upload format |
| Raster companion | Generated directly at 600 dpi |
| Scalar color scale | Cividis, ordered in grayscale |
| Secondary meaning | Explicit outlines, labels or markers; not color alone |
| Caption | Outside the artwork |

`figure_style.py` applies the profile with a local Matplotlib context rather
than changing global defaults for unrelated plots. Export checks reject text
smaller than the final-size range, overlapping labels and clipped text.
The PDF inspection separately checks actual dimensions, embedded fonts and
the absence of rasterized heatmap/colorbar data.

## PVT figure

The PVT artwork shows the maximum decision time among four input samples
at each of the 45 conditions. All cell labels are generated from the
verified measurement table; the full values remain in the CSV.
Black cell outlines mark conditions containing a missed secondary 1 ns
decision, so the distinction survives grayscale printing.

The local figure export and verification entry points are
`scripts/build_pvt45_figure.py` and `scripts/verify_pvt45_figure.py`.
They consume the checked final-result staging data and create a vector PDF,
SVG, high-resolution PNG, standalone caption and color/grayscale size proof.
They perform no circuit simulation and do not publish anything.

This is a figure-production convention for the competition, not an IEEE
certification, a publication decision or a change to the experimental results.

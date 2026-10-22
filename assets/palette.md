# Palette

Five colours, taken from the front page so the README, the report, the video and Devpost match what a judge already sees on the live demo. Each has a dark and a light value. Contrast is the WCAG ratio against that theme's background; 4.5:1 is the bar for small text, 3:1 for large text and graphics.

| Role | Used for | Dark | Contrast | Light | Contrast |
|---|---|---|---|---|---|
| Ground | page background | `#07070a` | n/a | `#fafaf6` | n/a |
| Ink | body text | `#f5f5f0` | 18.4:1 | `#0b0b0d` | 18.8:1 |
| Moved | an output that moved, a proven fix | `#c8ff3d` | 17.1:1 | `#467f00` | 4.7:1 |
| Silent | silent passthrough | `#ff4d4d` | 6.2:1 | `#d62828` | 4.8:1 |
| Phantom | phantom sensitivity | `#ffb020` | 11.0:1 | `#a35f00` | 4.8:1 |

The dark values are the front page's as they are. Two light values are darker than the front page's: its light lime `#4f8f00` is 3.8:1 and its light amber `#c77700` is 3.3:1, both under 4.5:1 for small text.

## Files

- `cover.png`: the Devpost cover, 1500×1000 (3:2).
- `thumbnail.png`: the video thumbnail, 1280×720.

Both use the dark values above and the fork tree of the recorded Sandboxes run: `question` load-bearing, `passages` a silent passthrough.

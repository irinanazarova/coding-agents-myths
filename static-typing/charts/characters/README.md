# Chart characters

The three characters on the charts come from the blog post's cover illustration. They were generated with Gemini (the nanobanana extension for Gemini CLI, model gemini-3.1-flash-image-preview), with the cover as the style and character reference, then cut out of their background with ImageMagick and saved as WebP. `charts.rb` embeds them in the SVGs, since a chart shown as an `<img>` can't load outside files.

| File | Prompt, after "Use cover.png as the style and character reference" |
| --- | --- |
| `martian-magnifier.webp` | The same green Martian, alone, full body, leaning forward and peering through the same pink magnifying glass at something small below and to the left. |
| `robot-printouts.webp` | The same pink robot, sitting on a tall stack of printed pages, reading a long scroll that curls down the stack, with a small stopwatch. |
| `martian-bug.webp` | The same green Martian, crouching and peering through the magnifying glass at a tiny red clay bug on the floor. |

Each prompt also asked for the cover's 3D clay style and lighting, no text or other objects, and a plain cream background.

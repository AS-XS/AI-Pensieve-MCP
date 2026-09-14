# Scene artwork and provider marks

The GUI loads every image locally from its installed package. No image-generation
service, CDN, or model is contacted when someone opens or uses Pensieve.

## Environment artwork

These four images were generated for this project with the built-in image
generation tool, then copied into the package without bitmap editing. The door
uses CSS clipping and two independently hinged leaves; the search transition
blends the chamber and overhead views. The apothecary bottle uses its own
cut-crystal illustration; its cork, smoke fill, and pouring motion are layered
locally with CSS and canvas.

- [Chamber](../src/archive_mcp/gui_assets/chamber.png)
- [Closed door](../src/archive_mcp/gui_assets/door.png)
- [Overhead basin](../src/archive_mcp/gui_assets/basin-overhead.png)
- [Apothecary bottle](../src/archive_mcp/gui_assets/apothecary-bottle.png)

The door and bottle outputs had dark surrounding backgrounds rather than true
transparency; the GUI clips their silhouettes in CSS.
The atmosphere follows the owner's wizarding-room concept. These are generated
illustrations, not extracted movie stills or game assets.

## Provider marks

Ten static SVG marks come from [LobeHub Icons](https://github.com/lobehub/lobe-icons),
package `@lobehub/icons-static-svg` version **1.95.0**: OpenAI, Codex, Claude, Gemini,
DeepSeek, Grok, Qwen, OpenCode, Antigravity, and NotebookLM. Their
[MIT license](../src/archive_mcp/gui_assets/logos/LICENSE.txt) is bundled beside
them. Marks identify source providers; they do not imply endorsement.

ChatGPT uses the OpenAI mark. Codex uses the distinct terminal-style Codex
emblem from the same pinned package; Claude formats share the Claude mark.
ZCode uses a plain `ZC` monogram rather than an unverified brand association.
Generic context uses a neutral symbol. The auto-detection bottle has no mark.
These images identify formats the existing adapters support; they do not add
support for arbitrary data from those companies.

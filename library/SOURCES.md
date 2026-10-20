# Sources checked

Licence per source, checked live (Iconify `collections` API reports each set's SPDX id; `lib icon add` and `lib graphic add` refuse anything off the allowlist in `libcore.ALLOWED`).

| Kind | Source | Licence | In library | Checked |
|---|---|---|---|---|
| icons | Lucide via Iconify | ISC | 60 starter icons | 2026-10-05 |
| icons | Tabler, Phosphor, Heroicons, Bootstrap Icons, Material Symbols, Simple Icons via Iconify | MIT / Apache-2.0 / CC0 | on demand (`lib icon add set/name`) | 2026-10-05 |
| graphics | Fluent Emoji Flat (Microsoft) via Iconify | MIT | 30 pictograms | 2026-10-05 |
| graphics | Noto Emoji (Google) via Iconify | Apache-2.0 | on demand (`lib graphic add` with the Iconify URL) | 2026-10-05 |
| lottie | LottieFiles free animations | Lottie Simple License | curated set in `lottie/`, each licence read on its page (`lib lottie add <url> --license Lottie-Simple --license-ok --page <page>`) | per file, see `.meta.json` |
| stock | Pexels, Pixabay, Unsplash | own licences | cache only, never in git | 2026-10-05 |
| stock music | Openverse (CC0 results, which are Freesound previews) | CC0-1.0 | cache only, never in git, no key, 20 results per request and 200 per day without a key | 2026-10-05 |

| animated icons | lucide-animated (pqoqubbw/icons) | MIT (drawings: Lucide, ISC) | all convertible icons in `icons-animated/lucide-animated/` | 2026-10-20 |
| icon metadata | Lucide repository `icons/*.json` (tags, categories) | ISC | folded into `INDEX.json` by `lib index` | 2026-10-20 |
| components | RemotionUI, Onda, Curvable motion | MIT | catalog in `upstream/`, rewritten parts in `fx/` | 2026-10-20 |
| components | remotion-bits | MIT in `package.json`, no LICENSE file (`licenses/remotion-bits-NOTE.md`) | catalog in `upstream/`, rewritten parts in `fx/` | 2026-10-20 |

Rejected:
| Source | Why | Checked |
|---|---|---|
| Lordicon | The free licence needs attribution and forbids sharing the icons as files or as an icon pack (https://lordicon.com/licenses, sections 2.4 i and ii). | 2026-10-20 |

Not added yet (need a manual licence and URL check first): unDraw, Open Peeps.
Brand logos (Simple Icons) are CC0 but the trademarks stay with the rights holders.

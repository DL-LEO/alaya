# Changelog

All notable changes to Alaya will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.9.0] - 2026-06-01

### Added
- **Session Boundary Protocol**: LLM detects conversation endpoints via weighted signals (explicit closing, persona switch, topic exhaustion) and prompts user to save memory
- **ambient.json semantic fields**: `mood_trajectory` (emotional arc, 3-entry cap), `recent_themes` (LLM-synthesized topic summary), `open_threads` (unresolved questions with lifecycle), `user_style_notes` (accumulated user preferences)
- **User-confirmed memory save**: both ambient.json (shared) and {persona}_history.json (isolated) are saved together at session boundary with explicit user confirmation
- **Rich ambient awareness**: Warm Recall Protocol now uses trajectory, themes, threads, and style notes for deeper persona awareness
- **Old-format ambient detection**: health_check and update_ambient auto-detect and initialize missing semantic fields
- **BI Observer (Rule G)**: passive pattern observer with three observation domains — affinity network dynamics (mutual growth, asymmetric, dense clusters), dormant persona detection (>14d inactive → gentle Tier 0 nudge), knowledge gap hints (interest area lacks wiki category or card count <5). No scoring, no ranking, no automatic intervention
- **bi_notes.json**: BI observation log (max 20 entries, append-only), stored in `alaya/memory/`, written by LLM at Session Boundary Save Protocol Step 5
- **bi_observer.py rewrite**: now reads all persona JSON + history files + ambient.json for real cross-persona pattern analysis (was: static persona config dump). Supports `--json` output for LLM consumption

### Changed
- **Level 1 xunxi batched**: no longer runs after every reply. All four operations (card boost, affinity, mood, attention) accumulate during session and execute ONCE at session boundary — zero fidelity loss, less overhead
- **update_ambient() refactored**: mechanical layer only (mood + trajectory + attention). Semantic fields preserved as-is — never overwritten by script
- **SKILL.md Rule C**: Level 1 retitled "At Session Boundary"; Agent no longer edits card files or runs scripts per-reply; tracks citations/tags/mood in memory for batched session-end execution
- **Save Protocol**: Level 1 script call integrated as Step 1 (mechanical), LLM semantic writes follow as Steps 2-4
- **SKILL.md Tier 0**: ambient loading now surfaces all 6 fields (mood, trajectory, themes, threads, style_notes, attention)
- **health_check.py [8]**: checks new ambient fields completeness; reports old-format ambient files
- **Level 2 triggers**: added session boundary detection as a trigger
- **Multi-persona / Group discussion**: card citations tracked for batch update at session boundary instead of immediate Level 1

### Design principle
- **Mechanical → script (auto)**: card strength, tag decay, affinity increment — no user involvement needed
- **Semantic → LLM (user-confirmed)**: themes, threads, style notes, persona history — user confirms at session boundary

## [1.8.0] - 2026-06-01

### Added
- **Emotional Memory System (方案C)**: per-persona interaction history with mood tracking + shared ambient state (recent_mood, recent_attention)
- **Warm Recall Protocol**: SKILL.md instructions for natural, character-voiced memory recall (structured data → warm output)
- **ambient.json**: shared cross-persona mood + attention state, stored in `alaya/memory/`
- **mood field**: interaction history entries now include user's emotional state (2-3 Chinese words)
- **attention weights**: tag frequency tracking with 0.7x decay + 0.3x boost, pruned below 0.1
- **Three-system architecture**: Knowledge / Memory / Persona subsystems with independent data directories and version numbers
- **config.json partitioning**: nested `knowledge`/`memory`/`persona` sections with per-system version fields
- **perfume_knowledge.py**: extracted knowledge operations (strength, decay, sleep, dirty tracking)
- **perfume_memory.py**: extracted memory operations (history hot/cold, ambient state, migration from manas/)
- **perfume_persona.py**: extracted persona operations (affinity increment and decay)
- **SKILL.md system markers**: `<!-- ALAYA:KNOWLEDGE -->`, `<!-- ALAYA:MEMORY -->`, `<!-- ALAYA:PERSONA -->` for section isolation
- **Auto-migration**: perfume.py auto-migrates flat config (v1.7) to nested structure (v1.8) and moves history files from manas/ to memory/
- **--mood parameter**: Level 1 xunxi accepts `--mood "开心"` for emotional state recording

### Changed
- **perfume.py**: rewritten as thin orchestrator (~100 lines), delegates to perfume_knowledge/memory/persona modules
- **Tier 0 loading**: now includes persona's hot zone history + ambient state (~200 tokens, always loaded)
- **SKILL.md**: added Three-System Architecture section, Warm Recall Protocol, updated all file paths (manas/ → memory/ for history)
- **Filesystem Convention**: new `alaya/memory/` directory for memory system data
- **config.json**: flat structure → nested `knowledge`/`memory`/`persona` sections

### Removed
- History files no longer stored in `manas/` (moved to `memory/`)

## [1.7.0] - 2026-06-01

### Added
- **Three-layer knowledge graph**: Layer 1 (wiki/index.md, concept network), Layer 2 (_category.md, card relations), Layer 3 (knowledge cards, leaf nodes)
- **Question-driven retrieval**: Tiers 1-2 are question-driven (not persona-driven); persona only intervenes at Tier 3 for card selection and interpretation
- **Category subfolders**: wiki/{category}/ structure replaces flat wiki/ for better organization
- **Cross-category links**: auto-generated from tag overlap (Concept Network in wiki/index.md)
- **Intra-category card relations**: auto-generated from tag overlap (Card Relations in _category.md)
- **Incremental index rebuild**: `--category` (single category) and `--incremental` (changed-only) modes
- **Dirty category tracking**: perfume.py marks categories dirty when strength crosses thresholds
- **AUTO/MANUAL section preservation**: build_index.py preserves user-edited content outside `<!-- AUTO -->` markers
- **format_converter.py**: zero-dependency format conversion (MD/TXT native, PDF via PyMuPDF optional)
- **batch_import.py**: batch import with checkpoint/resume, auto-scan + dedup, supports MD/TXT/PDF
- **Agent guidance template**: unsupported file formats trigger a template that guides the user's Agent to produce the right output
- **max_cards_per_persona**: configurable per-persona card selection limit (default 5)

### Changed
- **build_index.py**: complete rewrite — generates three-layer graph, injects missing metadata, supports incremental modes
- **SKILL.md Rule A**: retrieval reworked — question-driven Tiers 1-2, persona-driven Tier 3
- **import_paper.py**: supports `--category`, writes to wiki/{category}/, uses format_converter
- **health_check.py**: checks three-layer network integrity (broken links, orphans, bidirectionality, dirty categories)
- **perfume.py**: category-aware path resolution, skips _category.md, dirty category marking
- **fix_links.py**: category-aware card discovery, skips _category.md
- **setup_wizard.py**: version 1.7.0, max_cards_per_persona config step, updated post-setup instructions
- **docs/quick-start.md**: updated for three-layer graph, category subfolders, new commands
- **docs/role-guide.md**: added max_cards_per_persona documentation

### Removed
- **build_concepts.py**: cancelled — concept hub pages replaced by three-layer knowledge graph
- **scan_cards.py**: merged into build_index.py (metadata injection happens during index build)
- **seed_import.py**: replaced by batch_import.py
- **seeds/seed_index.json**: removed — card tracking now happens via _category.md files
- **alaya/seeds/ directory**: removed
- **alaya/index/ directory**: moved to wiki/ (index.md and _category.md)
- **wiki/concepts/ directory**: cancelled — three-layer graph replaces concept hub pages

## [1.6.0] - 2026-05-31

### Added
- **Persona profiles**: dual-file persona architecture (JSON config + Markdown profile.md) for richer character definition
- **8 persona profile.md files**: Feynman, Buddha, Zhuangzi, Socrates, Carl Jung, Galileo, Xiaozhao, Audrey Hepburn
- **Hot/Cold memory zones**: interaction history upgraded from flat FIFO to HOT (5 detailed) + COLD (45 compressed) with auto-rotation
- **Tags + Summary in history**: each interaction record now includes tags and one-line summary for better retrieval
- **Time-decay memory retrieval**: on-demand history search with decay weights (30d: 1.0, 30-60d: 0.5, 60d+: 0.3)
- **Persona Creation Protocol**: 7-phase distillation process for creating new personas via interview
- **Profile template**: `templates/persona_profile_template.md` for standard persona definition structure
- **Shared YAML utilities**: `scripts/lib/yaml_utils.py` eliminates frontmatter parsing duplication across 4 scripts
- **requirements.txt**: dependency declaration (Python standard library only, no external packages)
- **CHANGELOG.md**: this file
- **.gitignore**: excludes runtime artifacts, IDE files, and `.claude/` directory

### Changed
- **xunxi.py → perfume.py**: renamed cultivation engine with clearer naming
- **perfume.py**: `--tags` and `--summary` parameters for Level 1 history recording
- **setup_wizard.py**: extended interview creates both JSON and profile.md skeleton
- **persona_manager.py**: list/delete/clone/edit all handle companion profile.md files
- **scan_cards.py, seed_import.py, build_index.py, perfume.py**: use shared `yaml_utils` module

### Fixed
- **fix_links.py**: O(N×M×W) performance bug — `os.walk()` inside regex callback replaced with O(1) dict lookup
- **perfume.py**: `int()` argument parsing now gives clear error on non-numeric input
- **All personas**: removed copy-pasted affinity `{"feynman": {"score": 0.01}}` from initial configs
- **import_paper.py**: bare `except:` → `except Exception:`
- **setup_wizard.py**: hardcoded creation date → dynamic `datetime.now()`
- **README.md, docs/quick-start.md**: placeholder `{user}` → `DL-LEO`

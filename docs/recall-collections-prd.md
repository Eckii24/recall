# PRD: Recall Collections

## 1. Executive Summary

Recall currently models **one Markdown file as one deck**. That is clean, deterministic, and easy to reason about, but it breaks down for source layouts where the natural unit of authorship is **many Markdown files inside one topic folder**.

The next product step is a new concept: **Collection**.

A collection groups multiple Markdown source files into one learnable unit while preserving the current benefits of Recall:

- Markdown remains source of truth
- scheduling state remains explicit and Git-friendly
- the CLI stays headless and scriptable
- card provenance remains visible down to file and line

Primary motivating use case:

- `chess/`
- one file per analyzed game
- flashcards embedded directly in each game analysis
- learning should happen across the whole chess corpus, not one file at a time

This PRD recommends adding **collections as a first-class abstraction**, instead of overloading the existing deck model with hidden folder semantics.

---

## 2. Problem Statement

Recall's current model is too narrow for corpus-style learning.

Today:

- one file = one deck
- `next --deck <name>` reviews cards from exactly one file
- `review --deck <name> --card-id <id>` writes state for exactly one file-sidecar pair
- `scan` and `stats` can aggregate across decks, but **learning sessions cannot target a logical multi-file topic**

This creates friction in domains where the best authoring workflow is:

- content close to source
- one Markdown artifact per note, case, game, article, or incident
- cards embedded inline in those artifacts
- reviews aggregated at folder/topic level

Example pain:

- A chess folder with 200 game analyses is naturally one study domain
- In current Recall, that becomes 200 separate decks
- The user must choose one file/deck at a time
- There is no first-class "study all chess cards" workflow

The product gap is not card parsing. The gap is the missing abstraction between **single file** and **whole repo**.

---

## 3. Product Vision

Recall should support two authoring/storage shapes without forcing users to rewrite content organization:

1. **File Decks**
   - current behavior
   - one Markdown file = one learnable unit

2. **Collections**
   - one collection = many Markdown files
   - cards stay in their original files
   - learning, review selection, and stats can target the whole collection

Target outcome:

```text
Markdown files in folder
    ↓
Collection definition
    ↓
Recall aggregates cards across files
    ↓
Agent asks due cards across the collection
    ↓
User answers naturally
    ↓
Recall stores scheduling state with stable source provenance
```

The user should be able to keep domain knowledge in small source-local Markdown files without sacrificing a coherent study workflow.

---

## 4. Goals

### 4.1 Product Goals

1. Add a first-class **collection** concept to Recall.
2. Allow one collection to include multiple Markdown source files.
3. Preserve explicit card provenance: file path and line number.
4. Preserve stable scheduling state across refactors that do not change card identity.
5. Support learning sessions across all due cards in a collection.
6. Keep the CLI headless, deterministic, and agent-friendly.
7. Avoid breaking existing one-file deck workflows.
8. Keep migration cost low for existing repos.
9. Make collection behavior explicit in config and CLI, not implicit magic.
10. Leave room for future filters, tags, and sub-collections without requiring them now.

### 4.2 User Goals

The user wants to:

- embed flashcards directly inside source notes
- organize notes by folders that match real domains
- study across a whole folder/domain, not one file at a time
- keep Git-friendly plain text workflows
- avoid central aggregation files that duplicate content
- retain exact source traceability for every card

### 4.3 Agent Goals

The AI agent should be able to:

- request due cards for a whole collection
- present source metadata when useful
- review a specific card without ambiguity
- operate with stable machine-readable outputs
- avoid crawling arbitrary repo layout logic outside Recall itself

---

## 5. Non-Goals

### 5.1 Not in scope for this feature

- tags as a separate classification system
- nested collection inheritance rules beyond one simple level
- auto-generated cards from notes
- semantic deduplication of similar cards
- cross-repo collections
- remote sync or cloud storage
- UI/TUI redesign
- scheduler redesign
- review-history analytics
- per-card difficulty rubrics
- automatic move/rename detection based on fuzzy text similarity

### 5.2 Explicit anti-goals

This feature should **not**:

- silently reinterpret all folders as decks
- destroy the current file-deck mental model
- require users to merge many source files into one synthetic Markdown deck
- hide card provenance behind opaque collection-only IDs

---

## 6. Primary Use Cases

### 6.1 Chess analysis corpus

Structure:

```text
learning/chess/
  recall.config.json
  2026-06-05-lichess-t9bxRDQm-analysis.md
  2026-06-07-lichess-abcd1234-analysis.md
  openings/
    italian-game.md
```

Desired behavior:

- all files belong to one collection: `chess`
- each file may contain zero or more flashcards
- `recall next --collection chess` returns due cards across all files
- output includes `source.path` and `source.line`
- review state persists across sessions without flattening source files into a synthetic deck

### 6.2 Incident review knowledge base

- one Markdown file per incident
- flashcards embedded in postmortems
- study should happen across all incidents in `incidents/`

### 6.3 Article-based learning folder

- one Markdown file per article summary
- cards embedded inline
- reviews should target the thematic folder, not each article file separately

---

## 7. Recommendation

### 7.1 Product decision

Introduce a new top-level product abstraction:

- **Deck** = one Markdown file
- **Collection** = many Markdown files, explicitly configured

Do **not** redefine deck to mean both file and folder.

### 7.2 Why this is the right cut

Because two distinct user intents exist:

- "this one file is my unit of learning"
- "this folder of files is my unit of learning"

Those are related but not identical. If they share one overloaded term, CLI semantics become muddy fast.

### 7.3 Why not "folder = deck" as hidden behavior

Because it creates avoidable ambiguity:

- deck name currently maps directly to file name
- sidecar currently maps directly to one deck file
- `review` currently assumes one deck-sidecar scope
- folder-backed behavior needs multi-source aggregation and a different persistence story

Calling all of that a "deck" hides a real model boundary.

---

## 8. Conceptual Model

### 8.1 Core entities

#### Card

Unchanged logical meaning:

- question
- answer
- stable card ID
- source path
- source line

#### File Deck

Existing concept:

- one Markdown file
- local card set

#### Collection

New concept:

- named logical study unit
- includes one or more source files via explicit file/folder patterns
- can expose one aggregated due queue
- can expose one aggregated stats view

#### Review State

Scheduling state for cards.

Important constraint: review state must remain keyed by **stable card identity**, not by transient queue position.

### 8.2 Card identity requirements

Collection support only stays sane if card identity stays explicit and collision-safe.

Therefore:

- `recall:id` remains mandatory for reliable long-term use
- card IDs must be unique within the review scope used for lookup
- collection review must never depend on question text alone

Recommendation:

- require card IDs to be unique **within a collection**
- validation should fail if two files in the same collection define the same `recall:id`

That is stricter than file-local uniqueness, but it avoids review ambiguity and brittle composite lookup rules.

---

## 9. Configuration Model

### 9.1 Current limitation

Current config has a single `decks_dir` and assumes `*.md` files inside it are decks.

That is not expressive enough for collections.

### 9.2 Proposed config extension

Add a `collections` section to `recall.config.json`.

Illustrative shape:

```json
{
  "version": 2,
  "decks_dir": "decks",
  "default_auto_mode": false,
  "default_min_heading_level": 2,
  "sidecar_suffix": ".flashcards.json",
  "scheduler": "sm2",
  "collections": {
    "chess": {
      "include": [
        "chess/**/*.md"
      ]
    },
    "incidents": {
      "include": [
        "notes/incidents/**/*.md"
      ],
      "exclude": [
        "**/templates/**"
      ]
    }
  }
}
```

### 9.3 Design principles for config

- explicit include patterns
- optional exclude patterns
- repo-relative paths only
- deterministic expansion order
- no implicit collection creation from arbitrary folders in MVP

### 9.4 Why explicit config beats folder inference

Because explicit config:

- avoids accidental collection creation
- allows mixed layouts in one repo
- supports future naming independent of physical folder names
- is safer for automation and refactors

---

## 10. Persistence Model

This is the hardest product decision in the feature.

### 10.1 Requirement

Collection review state must be persisted in a way that is:

- explicit
- deterministic
- Git-friendly
- debuggable
- not tightly coupled to transient CLI output ordering

### 10.2 Recommendation

Use **one sidecar per collection**.

Example:

```text
learning/
  recall.config.json
  chess/
    2026-06-05-lichess-t9bxRDQm-analysis.md
    2026-06-07-lichess-abcd1234-analysis.md
  .recall/
    collections/
      chess.flashcards.json
```

Why this is better than per-source-file sidecars for collections:

- a collection is the review scope
- collection stats and due-queue are aggregated anyway
- one sidecar avoids fragmented state lookup across many files
- moving a card between files can preserve state if the `recall:id` stays stable

### 10.3 Sidecar key shape

Each stored card state should include at least:

- card ID
- source path last seen
- scheduling state

Illustrative shape:

```json
{
  "version": 1,
  "collection": "chess",
  "cards": {
    "italian-cct": {
      "source_path": "chess/2026-06-05-lichess-t9bxRDQm-analysis.md",
      "due": "2026-06-07",
      "ease": 2.5,
      "interval": 1,
      "reps": 1
    }
  }
}
```

### 10.4 Why not per-file sidecars for collection cards

Because then one logical study scope would be split across many persistence files, creating ugliness around:

- collection-level stats
- card move/rename behavior
- validation of cross-file uniqueness
- aggregated review operations

Per-file sidecars are still fine for file decks. Collections need their own storage boundary.

---

## 11. CLI Design

### 11.1 Core rule

The CLI must make the study scope explicit.

Do not overload `--deck` to sometimes mean file and sometimes folder.

### 11.2 Proposed commands

#### Learn next due cards

```bash
recall next --deck architecture
recall next --collection chess
```

Exactly one of `--deck` or `--collection` must be supplied for `next`.

#### Record review

```bash
recall review --deck architecture --card-id architecture-cqrs --rating good
recall review --collection chess --card-id italian-cct --rating good
```

Exactly one of `--deck` or `--collection` must be supplied for `review`.

#### Validate

```bash
recall validate --deck architecture
recall validate --collection chess
recall validate
```

`recall validate` without scope validates both file decks and collections.

#### Scan/stats

```bash
recall scan --collection chess --format json
recall stats --collection chess --format json
```

#### Discovery

```bash
recall collection list
recall collection show chess
```

### 11.3 Output requirements

Machine-readable output for collection cards must include:

- `collection`
- `card_id`
- `question`
- optional `answer`
- `source.path`
- `source.line`
- scheduling state

Example:

```json
{
  "collection": "chess",
  "cards": [
    {
      "card_id": "italian-cct",
      "question": "Was ist die zentrale Lehre dieser Partie?",
      "answer": "In scharfen Angriffsstellungen zuerst CCT prüfen: Checks, Captures, Threats.",
      "source": {
        "path": "chess/2026-06-05-lichess-t9bxRDQm-analysis.md",
        "line": 92
      },
      "state": {
        "due": "2026-06-07",
        "ease": 2.5,
        "interval": 1,
        "reps": 1
      }
    }
  ]
}
```

---

## 12. Validation Rules

### 12.1 Collection validation must check

1. collection name exists in config
2. include patterns resolve deterministically
3. resolved files exist and are readable
4. duplicate file inclusion does not create duplicate card loading
5. each included file parses successfully
6. card IDs are unique within the collection
7. source files do not collide with invalid config patterns
8. collection sidecar schema is valid

### 12.2 Validation warnings

Warnings should exist for:

- collection resolves to zero files
- file contains no cards
- sidecar contains orphaned card IDs no longer present in any source file
- last seen source path differs from current path for same card ID

### 12.3 Why warnings matter

Collections will be used on evolving note corpora. Drift is normal. The product must help users detect drift without treating every cleanup case as a fatal error.

---

## 13. Migration Strategy

### 13.1 Existing users

Existing file-deck users must see zero behavior change unless they opt into collections.

### 13.2 Opt-in migration

A user can add collections incrementally via config.

Example path:

1. Keep existing `decks/` workflow unchanged.
2. Add `collections.chess.include = ["chess/**/*.md"]`.
3. Run `recall validate --collection chess`.
4. Start using `recall next --collection chess`.

### 13.3 No forced migration of old sidecars

Collections are a new scope. Their sidecars should be created on first use.

If the same content previously existed as separate file decks, migrating old state into one collection sidecar is possible later, but should not block MVP.

---

## 14. Backward Compatibility

This feature must preserve:

- current config keys
- current file-deck commands
- current sidecar format for file decks
- current one-file parsing semantics

Breaking change to avoid:

- bumping existing repos into a new config version with different semantics unless they explicitly add collections

Recommendation:

- support config version 1 for old repos
- support config version 2 when `collections` is present

---

## 15. Risks and Trade-offs

### 15.1 Key risks

#### Risk 1: identity collisions across files

If two files define the same `recall:id` inside one collection, review state becomes ambiguous.

Mitigation:

- fail validation on duplicate IDs within a collection

#### Risk 2: state drift after note refactors

Cards may move between files or get deleted.

Mitigation:

- store `source_path` as metadata, not as primary key
- warn on orphaned or moved cards

#### Risk 3: config complexity creep

Collections can become a dumping ground for arbitrary query logic.

Mitigation:

- keep MVP to include/exclude globs only

#### Risk 4: overlapping scopes

A file may appear both as a file deck and in one or more collections.

Mitigation:

- allow it, but treat each scope as independent review state
- document clearly that review progress is not shared across scopes in MVP

This is not ideal, but it is honest and easier than magical state unification.

### 15.2 Trade-off: duplicated learning state across scopes

If the same card is reviewed once via file deck and once via collection, there may be two separate scheduling states.

That is ugly.

But forcing one shared universal state model across all possible scopes is a larger design problem and likely overkill for the first version.

Recommendation:

- accept duplicated state across different scopes in MVP
- optimize for explicitness over cleverness

---

## 16. Alternatives Considered

### Alternative A: Keep one file = one deck forever

Rejected because it fails the folder-corpus workflow.

### Alternative B: Treat folders as decks implicitly

Rejected because it overloads deck semantics, complicates persistence, and hides real product complexity.

### Alternative C: Require synthetic aggregation files

Rejected because it duplicates source content and breaks source-local authoring.

### Alternative D: Introduce tags instead of collections

Rejected because tags solve classification, not source aggregation and persistence scope.

---

## 17. Success Criteria

A successful MVP for collections means:

1. A configured collection can resolve multiple Markdown files.
2. `validate --collection <name>` succeeds on a healthy corpus.
3. `next --collection <name>` returns due cards across files with source metadata.
4. `review --collection <name> --card-id <id>` updates collection review state correctly.
5. `stats --collection <name>` reports aggregated collection numbers.
6. Existing file-deck workflows continue to work unchanged.
7. A user can embed flashcards in source-local files without creating synthetic mega-decks.

---

## 18. Acceptance Criteria

### 18.1 Functional acceptance criteria

- User can define at least one named collection in config.
- Collection can include Markdown files via repo-relative glob patterns.
- Collection commands exist for list/show/validate/scan/next/review/stats.
- Duplicate card IDs within one collection produce validation failure.
- Collection review state persists in a dedicated collection sidecar.
- JSON output includes source path and line.
- Empty collections produce clear warnings or errors, not silent no-ops.

### 18.2 Backward compatibility acceptance criteria

- Existing version-1 repos without collections still work.
- Existing `--deck` flows remain unchanged.
- File-deck sidecars remain readable and writable.

### 18.3 UX acceptance criteria

- CLI help clearly distinguishes deck vs collection.
- Scope ambiguity is rejected with explicit errors.
- Machine-readable outputs remain stable enough for agent automation.

---

## 19. Open Questions

These do not block the PRD, but they must be resolved before implementation locks.

1. Should a collection sidecar live under `.recall/collections/` or next to `recall.config.json` with a predictable name?
2. Should overlapping collections be allowed in MVP, or only warned about?
3. Should `scan` and `stats` without scope include collection totals, file-deck totals, or both separately?
4. Should `collection show <name>` expose the fully resolved file list for debugging?
5. Should collection-level `normalize` exist, or should normalization stay file-scoped only?

My recommendation:

- yes to `collection show`
- no to collection-level normalize in MVP
- allow overlapping collections, but warn

---

## 20. Final Recommendation

Build **collections as a first-class explicit feature**.

Do not pretend folders are just another kind of deck. They are not. They create a different review scope, different validation needs, and a different persistence boundary.

The right MVP is:

- explicit collections in config
- multi-file aggregation by glob
- one sidecar per collection
- collection-specific `next`, `review`, `scan`, `stats`, and `validate`
- strict duplicate-ID validation inside a collection
- zero regression for existing file-deck users

That gets Recall from **Markdown deck CLI** to **Markdown learning engine for note corpora**, which is the more durable direction.

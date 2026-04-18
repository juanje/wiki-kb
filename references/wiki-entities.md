# Wiki entities

## When to use

Load this reference alongside the active operation reference (ingest,
file, synthesize) when creating or processing entity-type content.

Entity pages use the same base format as concept pages but add a `type`
field in frontmatter and follow a type-specific template. Pages without
`type` are regular concept pages — backward-compatible.

## Entity vs concept — decision heuristic

| Signal | → Entity type | → Concept page |
|---|---|---|
| Has a proper name (capitalized, specific) | Likely entity (service, team, person, project) | — |
| Is an abbreviation or internal jargon | Glossary term | — |
| Has defined steps, trigger, cadence | Process | — |
| Is a recurring meeting with attendees | Meeting | — |
| Is a code repository with URL | Repository | — |
| Is a published piece with author, date, thesis | Article | — |
| Is an intellectual figure referenced across sources | Author | — |
| Is a step-by-step technical procedure or tutorial | Guide | — |
| Documents parameters, syntax, options, or API surface | Reference | — |
| Describes a pattern, principle, or abstract idea | — | Concept page |
| Can be instantiated (multiple "instances" exist) | — | Concept page |
| Has operational metadata (URL, owner, status) | Entity page | — |

## Entity types

### Glossary term (`type: glossary`)

Terms, abbreviations, and acronyms used internally.

```markdown
---
tags: [domain-tag]
type: glossary
origin: ingest | conversation | ephemeral
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Term or abbreviation]

**Full form:** [expanded form, if abbreviation]
**Domain:** [where this term is used]

[Definition — 2-3 sentences: what it means in context]

## Usage context
- [How and where this term appears in practice]
- [Common confusions or distinctions from similar terms]

## Connections
- [Related term](related-term.md) — [relationship]
- [Related concept](concept.md) — [relationship]
```

### Service or tool (`type: service`)

Internal services, tools, platforms, and systems.

```markdown
---
tags: [domain-tag]
type: service
origin: ingest | conversation | ephemeral
url: [primary URL, if applicable]
maintained_by: [team or person, if known]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Service/tool name]

[What it does — 2-3 sentences: purpose, who uses it, where it fits]

## Key facts
- **URL:** [link]
- **Access:** [how to get access]
- **Maintained by:** [team]

## How we use it
- [Specific use cases from our team's perspective]

## Connections
- [Related service](other-service.md) — [relationship]
- [Related concept](concept.md) — [relationship]
```

### Team (`type: team`)

Teams, squads, or organizational units.

```markdown
---
tags: [org-tag]
type: team
origin: ingest | conversation | ephemeral
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Team name]

[What the team does — 2-3 sentences: mission, scope, key responsibilities]

## Key people
- **[Role]:** [Name] — [brief context]

## What they own
- [Systems, services, or areas of responsibility]

## How we interact
- [How our team works with them]

## Connections
- [Related team](other-team.md) — [relationship]
- [Related service](service.md) — [they maintain it]
```

### Project (`type: project`)

Projects, initiatives, or epics.

```markdown
---
tags: [domain-tag]
type: project
origin: ingest | conversation | ephemeral
status: active | completed | paused | cancelled
jira: [VROOM-XXXXX or Epic link, if applicable]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Project name]

[What the project is — 2-3 sentences: goal, scope, why it matters]

## Key decisions
- [Decision with reasoning — date if known]

## Current state
- [Status and what's next]

## Connections
- [Related project](other-project.md) — [relationship]
- [Related service](service.md) — [project builds/modifies this]
- [Related team](team.md) — [stakeholder or contributor]
```

### Person (`type: person`)

People the user works with regularly.

```markdown
---
tags: [org-tag]
type: person
origin: ingest | conversation | ephemeral
team: [team name]
role: [job title or functional role]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Person name]

[Who they are — 1-2 sentences: role, team, what they're known for]

## Areas of expertise
- [What they know or own]

## How we interact
- [Working relationship, communication patterns]

## Connections
- [Team page](team.md) — member
- [Project page](project.md) — [role in project]
- [Related person](other-person.md) — [relationship]
```

### Process (`type: process`)

Recurring processes with defined steps: releases, certification
campaigns, onboarding, incident response.

```markdown
---
tags: [domain-tag]
type: process
origin: ingest | conversation | ephemeral
owner: [team or person responsible]
cadence: [frequency — e.g., "biweekly", "per release", "on demand"]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Process name]

[What this process accomplishes — 1-2 sentences]

## Trigger
- [What initiates this process]

## Steps
1. [Step with owner if relevant]
2. ...

## Inputs and outputs
- **Inputs:** [what's needed to start]
- **Outputs:** [what's produced]

## Connections
- [Related team](team.md) — [owns/participates]
- [Related service](service.md) — [used in step N]
```

### Meeting (`type: meeting`)

Recurring meetings with cadence, purpose, and participants.

```markdown
---
tags: [domain-tag]
type: meeting
origin: ingest | conversation | ephemeral
owner: [person who leads/organizes]
cadence: [e.g., "weekly", "biweekly", "monthly"]
day: [e.g., "Tuesday", "Thursday biweekly"]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Meeting name]

[Purpose of this meeting — 1-2 sentences]

## Attendees
- [Person or team] — [role in meeting]

## What happens
- [Typical agenda or focus areas]

## Connections
- [Related team](team.md) — [participates]
- [Related project](project.md) — [discussed here]
```

### Repository (`type: repository`)

Code repositories with URL, ownership, and purpose.

```markdown
---
tags: [domain-tag]
type: repository
origin: ingest | conversation | ephemeral
url: [repository URL]
maintained_by: [team or person]
language: [primary language, if applicable]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Repository name]

[What this repo contains and its role — 1-2 sentences]

## Key facts
- **URL:** [link]
- **Language:** [primary language]
- **Maintained by:** [team]
- **CI:** [CI system if relevant]

## What it does
- [Purpose and scope]

## Connections
- [Related service](service.md) — [repo implements this service]
- [Related project](project.md) — [part of this project]
```

### Article (`type: article`)

Published articles, blog posts, papers, talks, or any authored piece
worth referencing as a whole. The article entity captures the piece
itself; concepts extracted from it become separate concept pages linked
back via `## Connections`.

```markdown
---
tags: [domain-tag]
type: article
origin: ingest | conversation | ephemeral
author: [name or wiki page slug]
date: YYYY-MM-DD
publication: [blog name, journal, conference]
url: [canonical URL, if published online]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Article title]

[Abstract/summary — 2-5 sentences capturing the thesis and why it matters]

## Key arguments
- [Core argument or insight with reasoning chain]
- [Supporting argument — "because X, therefore Y"]

## Connections
- [Extracted concept](concept.md) — introduced in this article
- [Related article](other-article.md) — part of same series / responds to
- [Author page](author.md) — authored by
```

### Author (`type: author`)

Intellectual figures, researchers, writers, or thinkers referenced across
sources. Distinct from `person` (which models teammates and professional
contacts with `team`, `role`, "How we interact").

```markdown
---
tags: [domain-tag]
type: author
origin: ingest | conversation | ephemeral
field: [primary field or discipline]
url: [homepage, Wikipedia, or ORCID]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Author name]

[Who they are — 1-2 sentences: field, key contribution, relevance to the KB]

## Key contributions
- [Theory, book, framework, or body of work they are known for]

## Connections
- [Article page](article.md) — authored by
- [Related concept](concept.md) — originated or influenced
- [Related author](other-author.md) — collaborator or intellectual predecessor
```

### Guide (`type: guide`)

Technical procedures, tutorials, and how-tos that a reader follows
step by step. Distinct from `process` (which models recurring
organizational workflows like releases or onboarding).

```markdown
---
tags: [domain-tag]
type: guide
origin: ingest | conversation | ephemeral
difficulty: beginner | intermediate | advanced
prerequisites: [list or "none"]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Guide title]

[What the reader will accomplish — 1-2 sentences]

## Prerequisites
- [What is needed before starting]

## Steps
1. [Step with context and reasoning]
2. ...

## Connections
- [Related guide](other-guide.md) — next in sequence / alternative approach
- [Related concept](concept.md) — explains the theory behind this
- [Related reference](reference.md) — detailed parameter documentation
```

### Reference (`type: reference`)

API documentation, CLI references, configuration specs, or any
content that documents parameters, options, syntax, or fields.
Content meant to be consulted, not read linearly.

```markdown
---
tags: [domain-tag]
type: reference
origin: ingest | conversation | ephemeral
scope: api | cli | config | spec
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Reference title]

[What this documents — 1 sentence]

## Specification
- [Parameters, options, syntax, or fields with descriptions]

## Examples
- [Usage example with context]

## Connections
- [Related guide](guide.md) — uses this reference
- [Related service](service.md) — this is its reference doc
```

## Design principles

- **Same lifecycle as concepts.** Entity pages are created through any
  operation and maintained through lint.
- **`type` field is the discriminator.** Scripts use `type` in frontmatter
  for type-specific checks.
- **Templates are guidance, not rigid schemas.** Adapt to available info.
- **Entity pages connect to concept pages.** The value is the navigable
  network.
- **New types can be added.** Define a template here, add a `type` value,
  update `wiki-check.py`.

## Tagging guidelines

**Do not use entity types as tags.** The `type` field in frontmatter
already classifies the page. Tags like `person`, `service`, `team`,
`project`, `concept`, `glossary`, `process`, `meeting`, `repository`,
`article`, `author`, `guide`, `reference` are redundant and pollute
synthesis heuristics. Tags should describe the **domain** the entity
belongs to (e.g., `automotive`, `certification`, `ci-cd`), not the
entity category.

`concept` should never be used as a tag — it is the default page type
(pages without `type` are concepts).

## Glossary note

Glossary terms should always include a concise one-line definition
suitable for the consolidated `glossary.md`. For abbreviations, the
`**Full form:**` line is mandatory. The definition in the page
summary (first paragraph after the title) should be self-contained —
it appears verbatim in the glossary artifact.

## Type-specific extraction hints (for ingest)

- If the source mentions an internal tool name not in the wiki, consider
  a `service` entity page.
- If the source introduces an abbreviation or unfamiliar term, consider
  a `glossary` entity page.
- If the source names a team or organizational unit, consider a `team`
  entity page.
- If the source describes a project or initiative, consider a `project`
  entity page.
- If the source repeatedly references a specific person in a professional
  context, consider a `person` entity page.
- If the source describes a recurring workflow with defined steps
  (release process, onboarding, certification campaign), consider a
  `process` entity page.
- If the source mentions a recurring meeting with attendees and cadence,
  consider a `meeting` entity page.
- If the source references a code repository by URL or name, consider a
  `repository` entity page.
- If the source is a published article, blog post, or paper with a clear
  author, date, and thesis, consider an `article` entity page alongside
  the concept pages extracted from it.
- If the source repeatedly references an intellectual figure (researcher,
  author, thinker) who appears across multiple sources, consider an
  `author` entity page. Do not create one for casual mentions.
- If the source describes a technical procedure or tutorial that a reader
  follows step by step (install guide, setup walkthrough, how-to),
  consider a `guide` entity page.
- If the source documents API parameters, CLI options, configuration
  fields, or specification details meant for lookup rather than linear
  reading, consider a `reference` entity page.

## Type-specific lint checks

### Frontmatter fields

- Glossary pages for abbreviations should have a `Full form` field.
- Service pages should have a `url` or `maintained_by` field.
- Project pages should have a `status` field.
- Person pages should have a `team` field.
- Process pages should have an `owner` or `cadence` field.
- Meeting pages should have a `cadence` or `day` field.
- Repository pages should have a `url` or `maintained_by` field.
- Article pages should have an `author` or `date` field.
- Author pages should have a `field` field.
- Guide pages should have a `difficulty` field.
- Reference pages should have a `scope` field.

### Required body sections

Each entity type has minimum expected sections. Missing sections are
reported as info-level findings (not auto-fixable):

| Type | Required sections |
|---|---|
| glossary | `Usage context`, `Connections` |
| service | `Key facts`, `Connections` |
| team | `Key people`, `What they own`, `Connections` |
| project | `Key decisions`, `Current state`, `Connections` |
| person | `Areas of expertise`, `Connections` |
| process | `Steps`, `Connections` |
| meeting | `Attendees`, `Connections` |
| repository | `Key facts`, `Connections` |
| article | `Key arguments`, `Connections` |
| author | `Key contributions`, `Connections` |
| guide | `Steps`, `Connections` |
| reference | `Specification`, `Connections` |

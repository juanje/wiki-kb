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
`project`, `concept`, `glossary` are redundant and pollute synthesis
heuristics. Tags should describe the **domain** the entity belongs to
(e.g., `automotive`, `certification`, `ci-cd`), not the entity
category.

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

## Type-specific lint checks

- Glossary pages for abbreviations should have a `Full form` field.
- Service pages should have a `url` or `maintained_by` field.
- Project pages should have a `status` field.
- Person pages should have a `team` field.

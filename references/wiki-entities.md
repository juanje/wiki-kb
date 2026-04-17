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
`project`, `concept`, `glossary`, `process`, `meeting`, `repository`
are redundant and pollute synthesis
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
- If the source describes a recurring workflow with defined steps
  (release process, onboarding, certification campaign), consider a
  `process` entity page.
- If the source mentions a recurring meeting with attendees and cadence,
  consider a `meeting` entity page.
- If the source references a code repository by URL or name, consider a
  `repository` entity page.

## Type-specific lint checks

### Frontmatter fields

- Glossary pages for abbreviations should have a `Full form` field.
- Service pages should have a `url` or `maintained_by` field.
- Project pages should have a `status` field.
- Person pages should have a `team` field.
- Process pages should have an `owner` or `cadence` field.
- Meeting pages should have a `cadence` or `day` field.
- Repository pages should have a `url` or `maintained_by` field.

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

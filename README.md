# Productive Value–Productive Power (PV-PP) Framework

This is the curated public repository for the Productive Value–Productive Power (PV-PP) research program.

The PV-PP framework models decision and action in terms of productive value, productive power, perceived decision state, viability, governing domains, policy construction, feasibility, restoration adequacy, selection, realization, and state transition.

This repository is intentionally curated. It contains the current public framework architecture and selected supporting material. Developmental, private, superseded, implementation-internal, and unpublished research materials remain outside this repository.

## Repository Structure

### 10 Core Framework

Current public core framework specifications, including Layer 1, Layer 2 core architecture, the graph layer, perception and state interfaces, and supporting architectural specifications.

### 15 Operators

Current public operator-owner specifications and selected operator-supporting specifications.

### 20 Stack and Layer Governance

Governance, ownership, stack maps, reader guidance, invariants, diagrams, and layer/interface documentation used to interpret the framework correctly.

### 30 Applications and Extensions

A deliberately limited set of Layer 3 and Layer 4 application and extension materials.

This area includes material whose status is explicitly identified as provisional-canonical or exploratory where applicable. Inclusion in this repository does not elevate such material to canonical status.

### 40 Runtime and Execution Formalization

A narrow public runtime-architecture surface consisting of the interface ladder, setup and domain-frame guidance, tool-action admission boundary, and static governance examples.

Internal implementation artifacts, code, prototype records, validation materials, and internal-use-only sidecar documents are not included.

### 50 Scalar Reduction Proof Program

The formal Scalar Reduction Proof Program is maintained in a separate public repository.

Category 50 contains a README pointing to the authoritative proof repository rather than duplicating its files.

This preserves a single authoritative public source for the proof program and prevents version divergence between repositories.

### 60 Benchmarks and Simulations

The broader benchmark and simulation workstream is not reproduced in this repository.

Category 60 instead indexes benchmark projects that have been deliberately promoted to standalone public repositories.

The currently referenced public benchmark projects are:

- PV-PP Agent Decision Layer Demo
- Grenade Self-Sacrifice Benchmark
- AI Gridworld Safe Benchmark

Their dedicated repositories remain authoritative for their respective benchmark materials.

## Deliberately Omitted Material

The internal PV-PP research tree is substantially larger than this public repository.

It contains additional exploratory research, unpublished and submitted papers, books, intellectual-property material, implementation work, prototype development, research simulations, publication material, project-management infrastructure, and other working files.

Their absence from this repository is deliberate.

In particular:

- Category 70 exploratory and future-promotion research is not part of this public framework release.
- Unpublished and submitted Category 80 research papers are not reproduced here.
- Later internal project, publication, intellectual-property, marketing, documentation, and work-management directories are outside the scope of this repository.

The public repository should therefore not be interpreted as an inventory of all PV-PP research.

## Authority

Public availability does not by itself make a document canonical.

Where documents conflict, current owner specifications and current governance or authority documents control over older drafts, historical architecture, summaries, examples, benchmarks, publication material, implementation artifacts, and exploratory extensions.

Document status remains significant. Canonical, supporting, provisional-canonical, exploratory, application, example, and benchmark materials do not carry identical authority.

See `AUTHORITY_AND_STATUS.md` for the repository's authority rules and status vocabulary.

## Specialized Public Projects

Some PV-PP research programs are large enough to maintain their own public repositories.

The main PV-PP framework repository therefore serves both as a framework repository and as a top-level map to specialized public projects.

Categories 50 and 60 provide links to those independently maintained projects rather than duplicating their contents.

## Release Status

This repository represents a curated public framework release assembled after an authority and documentation-hygiene review of the working PV-PP research tree in August 2026.

See `RELEASE_NOTES.md` for release-scope details.
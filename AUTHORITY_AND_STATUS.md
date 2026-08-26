# Authority and Status

## Purpose

This file explains how authority works inside the public Productive Value–Productive Power (PV-PP) framework repository.

The repository contains canonical, supporting, provisional-canonical, application, exploratory, benchmark-reference, and explanatory materials.

These categories are not equivalent.

A document does not become authoritative merely because it is public, appears in a numbered directory, or contains the word "canonical" in an older title.

## Controlling Rule

**Current owner files govern.**

Where two documents conflict, the current owner specification or current governance document controls over:

- older drafts and superseded revisions;
- historical architecture;
- testing notebooks and simulation artifacts;
- benchmark-specific descriptions;
- publication summaries;
- implementation examples;
- application material;
- provisional or exploratory extensions;
- explanatory diagrams; and
- reader guides.

## Operator Ownership

Operator internals are governed by their current operator-owner specifications.

Supporting documents may describe interfaces, constraints, construction procedures, parameterization, integration boundaries, or other supporting architecture, but they do not silently redefine an owned operator.

The current public ownership and stack surfaces are maintained in Category 20.

## Core State and Interface Authority

Layer 1 owns actual state and transition semantics.

The current perception architecture owns the structured perceived decision-state interface used by Layer 2.

Perceived Productive Power (PPP) is a component of that perceived decision state rather than a synonym for the complete perceived state.

Downstream operators consume only the state and interface portions licensed by their owning specifications.

## Status Vocabulary

### Canonical

A controlling specification within its declared ownership scope.

Canonical status should not be inferred outside that scope.

### Supporting Specification

An authoritative support document within a bounded interface or architectural role.

A supporting specification does not supersede an owner specification unless an explicit authority document says otherwise.

### Provisional Canonical / Promotion Candidate

Material considered sufficiently developed for controlled use but not fully promoted to canonical authority.

Promotion requirements stated in the document remain binding.

Presence in the public repository does not itself constitute promotion.

### Exploratory

Research material investigating extensions, scaling behavior, alternative formulations, or future architecture.

Exploratory material does not modify canonical framework semantics merely by being present in the repository.

### Application / Example

A downstream use, case analysis, or illustration of the framework.

Applications and examples do not independently redefine the framework.

### Benchmark / Simulation

Evidence-generating, testing, or diagnostic artifacts.

Benchmark and simulation results may expose defects, support revisions, test behavior, or motivate additional research, but they do not automatically become framework authority.

## Specialized Repositories

The Scalar Reduction Proof Program and promoted benchmark projects are maintained in dedicated public repositories.

Their files are intentionally not duplicated here.

For those projects, the dedicated repository is the authoritative public location for project-specific materials.

The Category 50 and Category 60 README files provide the corresponding public references.

## Superseded and Internal Material

Superseded revisions, archives, review-for-future-integration material, internal-use-only implementation documents, private research, unpublished manuscripts, and working research artifacts are intentionally excluded from this public repository.

Their exclusion is part of the authority-hygiene design.

It should not be interpreted as evidence that the broader PV-PP research program does not contain such work.

## Interpretation Rule

When using this repository for analysis, implementation, citation, or AI-assisted retrieval:

1. Identify the document's declared status.
2. Determine whether the document owns the concept, interface, or operator being interpreted.
3. Prefer the current owner or governance surface over summaries, examples, historical documents, and older revisions.
4. Preserve explicit boundaries between actual state, perceived state, operator interfaces, execution, and downstream applications.
5. Do not promote provisional, exploratory, application, benchmark, simulation, or example material into canonical framework semantics without an explicit promotion or authority action.

## Public Does Not Mean Canonical

The repository intentionally exposes some material that is useful for understanding the development, application, or research frontier of PV-PP without granting that material canonical authority.

Accordingly:

**Public availability is a publication status. Canonical authority is an architectural status.**

The two should not be conflated.
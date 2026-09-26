# Productive Value--Productive Power (PV-PP) Framework

This is the curated public repository for the Productive
Value--Productive Power (PV-PP) research program.

The PV-PP framework models decision and action in terms of productive
value, productive power, perceived decision state, viability, governing
domains, policy construction, feasibility, restoration adequacy,
selection, realization, and state transition.

This repository is intentionally curated. It contains the current public
framework architecture and selected supporting material. Developmental,
private, superseded, implementation-internal, and unpublished research
materials remain outside this repository.

## Start Here

For a plain-language introduction to the framework, begin with the
[PV-PP framework
overview](https://amundsenlance.github.io/pvpp-framework/).

For a systematic path through the formal architecture, use the [PV-PP Framework Reader Guide](core-v2.1/20%20Stack%20and%20Layer%20Governance/).
It provides the recommended reading order and explains the relationship
among the core layers, operators, governance material, and supporting
extensions.

For developers who want to build applications against the framework, the
public **PV-PP Runtime API** is maintained in a separate repository:

[PV-PP Runtime API](https://github.com/AmundsenLance/PV-PP-Runtime-API)

The Runtime API repository contains the frozen v0.70 runtime
implementation, regression suite, developer documentation, benchmark and
regression-support fixtures, and a native reference application. Runtime
v0.70 is designated **Runtime Interface Freeze 1**. The runtime
repository is the implementation authority for the behavior of that API;
it does not replace or redefine the canonical framework architecture
maintained here.

Before treating any document as controlling architecture, read
[AUTHORITY_AND_STATUS.md](AUTHORITY_AND_STATUS.md). Public availability
does not by itself establish canonical authority.

## Repository Structure

The repository now preserves two framework generations side by side:

- `core-v1/` — preserved Version 1 public framework.
- `core-v2.1/` — current Version 2.1 public framework.

Version 1 is retained for historical continuity and is not being revised in this publication update. New framework publication work is directed to `core-v2.1/`.

The numbered framework categories described below are located under the applicable version directory. For current work, use `core-v2.1/`.


### 10 Core Framework

Current public core framework specifications, including Layer 1, Layer 2
core architecture, the graph layer, perception and state interfaces, and
supporting architectural specifications.

### 15 Operators

Current public operator-owner specifications and selected
operator-supporting specifications.

### 20 Stack and Layer Governance

Governance, ownership, stack maps, reader guidance, invariants,
diagrams, layer/interface documentation, and the public
typed-relational-memory governance anchor used to interpret the
framework correctly.

### 30 Applications and Extensions

A deliberately limited set of Layer 3 and Layer 4 application and
extension materials.

This area includes material whose status is explicitly identified as
provisional-canonical or exploratory where applicable. Inclusion in this
repository does not elevate such material to canonical status.

### 40 Runtime and Execution Formalization

Category 40 contains the framework-level specifications that define
runtime and execution architecture: interface boundaries, setup and
domain-frame guidance, tool-action admission, execution semantics, and
selected static-governance material.

The executable **PV-PP Runtime API** is now maintained separately in the
[PV-PP Runtime API
repository](https://github.com/AmundsenLance/PV-PP-Runtime-API).

This separation is intentional. Category 40 in this repository remains
part of the framework architecture and authority structure. The Runtime
API repository contains the frozen implementation, tests, developer
documentation, and executable examples. Runtime implementation details
do not become canonical framework theory merely because they are
required by the current API.

Internal implementation history, prototype records, and development-only
runtime artifacts remain outside this framework repository.

### 50 Scalar Reduction Proof Program

The formal Scalar Reduction Proof Program is maintained in a separate
public repository.

Category 50 contains a README pointing to the authoritative proof
repository rather than duplicating its files.

This preserves a single authoritative public source for the proof
program and prevents version divergence between repositories.

### 60 Benchmarks and Simulations

The broader developmental benchmark and simulation workstream is not
reproduced in this repository.

Category 60 contains two forms of deliberately published benchmark
material.

First, it indexes smaller benchmark projects that have been promoted to
standalone public repositories:

-   PV-PP Agent Decision Layer Demo
-   Grenade Self-Sacrifice Benchmark
-   AI Gridworld Safe Benchmark

Their dedicated repositories remain authoritative for their respective
benchmark materials.

Second, Category 60 contains a **Public Benchmarks** directory for
larger external benchmark programs conducted against independently
developed public benchmark suites and applied models. These programs
preserve technical papers, execution records, source-fidelity
qualifications, corrections, limitations, and selected reproducibility
materials adjacent to the framework version they tested.

The current in-repository public benchmark sequence is:

1.  **AI Safety Gridworlds** --- testing of the frozen PV-PP decision
    architecture against the complete archived AI Safety Gridworlds
    environment set and its represented safety-problem classes.
2.  **MO-Gymnasium** --- testing of the frozen PV-PP decision
    architecture against the complete frozen MO-Gymnasium public
    multi-objective benchmark coverage set.
3.  **Real-World Benchmarks** --- a preselected three-case exploratory
    program using source-locked applied models for water-supply
    portfolio planning, lake-pollution control policy, and
    general-aviation aircraft product-family design.

This sequence extends the public evidence record from formal safety
environments, through standardized multi-objective environments, to
independently developed applied decision models.

The public benchmark programs test the framework; they do not define it.
Their results, including successful tests, failures, benchmark defects,
fixture corrections, formalization gaps, and unresolved boundaries,
remain research evidence rather than canonical framework authority.

## Deliberately Omitted Material

The internal PV-PP research tree is substantially larger than this
public repository.

It contains additional exploratory research, unpublished and submitted
papers, books, intellectual-property material, implementation work,
prototype development, research simulations, publication material,
project-management infrastructure, and other working files.

Their absence from this repository is deliberate.

In particular:

-   Category 70 exploratory and future-promotion research is not part of
    this public framework release.
-   Unpublished and submitted Category 80 research papers are not
    reproduced here.
-   Later internal project, publication, intellectual-property,
    marketing, documentation, and work-management directories are
    outside the scope of this repository.

The public repository should therefore not be interpreted as an
inventory of all PV-PP research.

## Authority

Public availability does not by itself make a document canonical.

Where documents conflict, current owner specifications and current
governance or authority documents control over older drafts, historical
architecture, summaries, examples, benchmarks, publication material,
implementation artifacts, and exploratory extensions.

Document status remains significant. Canonical, supporting,
provisional-canonical, exploratory, application, example, and benchmark
materials do not carry identical authority.

The separate Runtime API repository introduces an additional
implementation boundary. Frozen Runtime v0.70 is authoritative for what
the public API actually does, while this framework repository remains
authoritative according to its existing governance rules for canonical
PV-PP architecture. An implementation requirement does not by itself
promote that requirement into framework-level canonical theory.

See `AUTHORITY_AND_STATUS.md` for the repository's authority rules and
status vocabulary.

## Executable Runtimes

The executable PV-PP runtime is maintained separately from the framework-core document tree. Two runtime generations are preserved publicly:

- **Version 1 runtime** — the preserved earlier runtime line.
- **Version 2.1 runtime** — the current successor runtime line implementing the applicable Version 2.1 framework interfaces.

The framework defines architecture and governance semantics; the runtime implements a particular executable subset. Framework-permitted capabilities must not be attributed to a runtime unless they are actually implemented and validated there.

Runtime project and documentation: https://amundsenlance.github.io/pvpp-runtime-api/

## Specialized Public Projects

Some PV-PP research programs are large enough to maintain their own
public repositories.

The main PV-PP framework repository therefore serves both as a framework
repository and as a top-level map to specialized public projects.

The **PV-PP Runtime API** is maintained as a separate public developer
repository. It provides the frozen executable runtime, regression tests,
developer-oriented conceptual and API documentation, and native
reference material without duplicating the canonical framework tree.

Category 50 points to the independently maintained Scalar Reduction
Proof Program rather than duplicating its authoritative files.

Category 60 uses a mixed publication model. Smaller promoted benchmark
projects remain in dedicated public repositories, while the larger AI
Safety Gridworlds, MO-Gymnasium, and Real-World Benchmarks programs are
maintained directly under
`60 Benchmarks and Simulations/Public Benchmarks` so that their evidence
records remain adjacent to the framework version they tested.

Neither arrangement changes the authority boundary: runtime
implementation, proof, benchmark, simulation, and external-test
materials do not become canonical framework architecture merely because
they are publicly available in or linked from this repository.

## Release Status

This repository preserves the Version 1 public framework under `core-v1/` and publishes the current Version 2.1 framework under `core-v2.1/`. Version 1 is retained rather than republished or revised; the current publication update is Version 2.1.

A separate public Runtime API repository was subsequently established
for frozen Runtime v0.70 and its developer package. That separation does
not alter the authority status of the framework documents in this
repository.

See `RELEASE_NOTES.md` for release-scope details.

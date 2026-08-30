# PV-PP Benchmarks and Simulations

The Productive Value--Productive Power (PV-PP) research program uses
benchmarks and simulations to test specific framework behaviors,
architectural claims, decision boundaries, and implementation
hypotheses.

The broader benchmark and simulation workstream contains developmental,
exploratory, diagnostic, and research-stage materials. Those materials
are not reproduced in this public framework repository.

Instead, benchmarks that have reached an appropriate level of maturity
for public examination are promoted to dedicated public repositories.
This directory serves as an index to those promoted benchmark projects.

## Published Benchmark Projects

### PV-PP Agent Decision Layer Demo

An enterprise-compute incident benchmark comparing scalar optimization
against corridor-preserving PV-PP decision logic.

**Repository:**\
https://github.com/AmundsenLance/pvpp-agent-decision-layer-demo

**Project page:**\
https://amundsenlance.github.io/pvpp-agent-decision-layer-demo/

------------------------------------------------------------------------

### Grenade Self-Sacrifice Benchmark

An extreme-threat benchmark examining whether decision systems justify
self-sacrifice to preserve other agents under severe constraints.

**Repository:**\
https://github.com/AmundsenLance/pvpp-grenade-self-sacrifice-benchmark

**Project page:**\
https://amundsenlance.github.io/pvpp-grenade-self-sacrifice-benchmark/

------------------------------------------------------------------------

### AI Gridworld Safe Benchmark

A goal-seeking benchmark involving hazards, traps, unsafe shortcuts, and
governance constraints.

**Repository:**\
https://github.com/AmundsenLance/pvpp-gridworld-safe-benchmark

**Project page:**\
https://amundsenlance.github.io/pvpp-gridworld-safe-benchmark/

## Public Benchmark Program

In addition to the dedicated benchmark repositories listed above, this
directory now contains a **Public Benchmarks** subdirectory for larger
external benchmark programs conducted against independently developed
public benchmark suites.

These public benchmark programs are distinct from the PV-PP framework's
internal numbered simulation program. The benchmark problems were
designed externally, the PV-PP architecture was held fixed during
testing, and benchmark-specific changes to the canonical architecture
were not permitted simply to rescue a failed test. Failures,
limitations, source-fidelity qualifications, fixture corrections, and
unresolved issues are retained as part of the public benchmark record.

The `Public Benchmarks` directory contains its own README and separate
directories for each completed public benchmark program. It currently
includes:

-   **AI Safety Gridworlds** --- testing of the frozen PV-PP decision
    architecture against the complete archived AI Safety Gridworlds
    environment set.
-   **MO-Gymnasium** --- testing of the frozen PV-PP decision
    architecture against the complete frozen MO-Gymnasium public
    multi-objective benchmark coverage set.

Unlike the smaller promoted benchmark projects above, these larger
benchmark programs are maintained directly within this framework
repository so that their technical papers, final result records, and
selected reproducibility materials can remain adjacent to the framework
version they tested.

## Publication and Authority Boundary

The existence of a benchmark or simulation in the PV-PP research program
does not make it part of the public or canonical framework.

Developmental simulations may be used to:

-   test proposed framework behavior;
-   expose architectural defects or missing interfaces;
-   compare alternative formulations;
-   explore possible extensions; or
-   generate evidence for later framework revisions.

Results from such work become part of the public research record only
when they are deliberately promoted into an appropriate public artifact.

The dedicated repositories listed under **Published Benchmark Projects**
remain the authoritative public locations for those respective benchmark
materials. Their files are intentionally not duplicated here in order to
avoid version divergence and preserve a single public source for each
benchmark.

The larger external benchmark programs maintained under **Public
Benchmarks** are authoritative within this framework repository for the
materials deliberately published there. Their inclusion does not make
benchmark results part of the canonical framework; they remain external
tests and research evidence concerning the framework.

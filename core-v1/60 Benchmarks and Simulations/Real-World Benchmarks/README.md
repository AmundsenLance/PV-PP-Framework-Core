# PV-PP Benchmark Program

This directory is the top-level home for benchmark and simulation
evidence developed for the Productive Value-Productive Power (PV-PP)
framework.

The benchmark program tests the framework at several levels, ranging
from internally constructed stress environments to standardized public
benchmark suites and independently developed applied decision models.
These categories serve different evidentiary purposes and should not be
treated as interchangeable.

PV-PP is evaluated as a **decision architecture**. Benchmark results are
evidence about the behavior, representational capacity, limits, and
failure modes of the frozen framework under specified test conditions.
They do not by themselves redefine canonical PV-PP architecture.

## Directory Structure

### Internal Benchmarks

`Internal Benchmarks` contains constructed benchmark environments
developed specifically to stress important portions of the PV-PP
architecture.

These benchmarks can exercise combinations of features that may be
difficult to isolate in existing external environments, including
heterogeneous agents, persistent productive capacity, productive-value
exchange, resource dependencies, contractual commitments, incomplete
information, recovery pathways, irreversible losses, and dynamic
multi-period interaction.

The principal current internal benchmark is the **Asterion Benchmark
V2**, a stochastic multi-agent productive-system benchmark. Its public
record includes the benchmark-definition documents, the frozen final M14
execution package, banking and validation records, and the benchmark
white paper.

Internal benchmarks are designed tests. Their evidentiary value
therefore depends heavily on prospective specification, frozen
architecture, controlled comparator construction, common-random-number
execution where applicable, preservation of diagnostic failures, and
transparent validation.

### Public Benchmarks

`Public Benchmarks` contains testing against standardized benchmark
environments developed outside the PV-PP project.

The current public benchmark programs include:

-   **AI Safety Gridworlds**, used to test behavior against
    independently designed safety mechanisms and failure modes; and
-   **MO-Gymnasium**, used for systematic testing across standardized
    multi-objective environments and for examining scalar-reduction
    boundaries.

Because these environments were not designed for PV-PP, they provide an
important external check on whether the framework can operate coherently
outside internally constructed test worlds.

### Real-World Benchmarks

`Real-World Benchmarks` contains source-locked testing against
independently developed applied decision models.

The first completed program uses the MOEA Framework
**RealWorldBenchmarks** collection and includes:

-   Lower Rio Grande Valley water-supply portfolio planning;
-   lake-pollution control policy; and
-   general-aviation aircraft product-family design.

These tests ask whether the frozen PV-PP architecture can represent and
execute externally defined applied problems while preserving the
variables, constraints, objectives, uncertainty, dynamics, and
consequence structures treated as decision-relevant by the source model.

## Benchmark Progression

The benchmark program has developed through increasingly demanding forms
of evidence:

1.  **Internal simulations and architecture regressions** --- controlled
    tests of individual framework mechanisms and interactions.
2.  **AI Safety Gridworlds** --- externally designed safety mechanisms
    and failure modes.
3.  **MO-Gymnasium** --- standardized multi-objective benchmark
    environments.
4.  **Real-World Benchmarks** --- independently developed applied
    decision models.
5.  **Asterion Benchmark V2** --- an integrated stochastic multi-agent
    productive-system stress benchmark exercising a large portion of the
    frozen PV-PP architecture simultaneously.

This progression should not be interpreted as a single ranking of
benchmark importance. Each category answers a different methodological
question.

## General Benchmark Rules

Across the benchmark program, the governing research discipline is to:

-   define the benchmark question and relevant test conditions before
    interpreting outcomes;
-   distinguish canonical framework architecture from benchmark-specific
    fixtures and environment rules;
-   hold the tested PV-PP architecture fixed during a production run;
-   avoid adding benchmark-specific operators merely to rescue an
    unfavorable result;
-   preserve common random numbers or other controlled comparison
    structures where the benchmark permits them;
-   distinguish architecture failures from benchmark defects,
    implementation defects, search failures, fixture errors, translation
    errors, comparator failures, and formalization gaps;
-   preserve unfavorable results, superseded builds, material
    corrections, qualifications, and unresolved boundaries when they are
    necessary to understand the evidentiary lineage; and
-   avoid converting heterogeneous benchmark outcomes into a universal
    PV-PP score unless such a reduction is independently justified.

Not every developmental artifact belongs in the public repository.
Public benchmark directories are curated research records containing the
materials necessary to understand, reproduce, audit, and interpret the
relevant benchmark. Complete internal working archives may contain
additional intermediate files.

## Interpretation Boundary

Successful benchmark performance does not establish that PV-PP is
universally superior to scalar optimization, multi-objective
optimization, model-predictive control, reinforcement learning, or any
other decision architecture.

Likewise, failure in a particular benchmark does not automatically
establish a canonical architectural failure.

The proper interpretation is benchmark-relative: what the frozen
architecture represented, selected, preserved, or failed to preserve
under the specified environment, information conditions, comparator
definitions, and execution rules.

Where benchmark evidence identifies a possible architectural issue, that
issue must pass through the framework's normal controlled research and
promotion process before it can alter canonical PV-PP authority.

## Reproducibility and Historical Record

Individual benchmark directories contain their own README files
describing the benchmark-specific structure, authority boundary,
execution artifacts, validation records, and interpretation limits.

Where a benchmark has undergone material correction or supersession, the
public record should retain enough lineage to explain the change without
reproducing the entire internal development workspace.

The objective of this repository is therefore not to publish every file
created during benchmark development. It is to maintain a clear,
auditable, and reproducible record of the evidence produced by the PV-PP
benchmark program.

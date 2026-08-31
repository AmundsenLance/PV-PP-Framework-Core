# PV-PP Real-World Benchmarks

This directory is the top-level home for real-world benchmark programs
conducted against the Productive Value-Productive Power (PV-PP)
framework.

Real-world benchmarks extend the PV-PP testing program beyond
constructed internal simulations and standardized formal benchmark
suites. The purpose is to test the frozen framework against
independently developed applied decision models whose variables,
constraints, objectives, uncertainty, dynamics, and consequence
structures were defined outside the PV-PP project.

## Purpose

The governing question for this category is:

> Can the frozen PV-PP architecture faithfully represent externally
> defined applied decision problems while preserving the distinctions
> the source problem itself treats as decision-relevant?

PV-PP is evaluated here as a **decision architecture**, not as a
replacement optimization, search, learning, control, or domain-specific
modeling algorithm.

A real-world benchmark is not considered successful merely because its
terminology can be translated into PV-PP language. The source problem's
actual structure must survive the mapping and execution.

## Program Rules

Real-world benchmark programs in this directory should:

-   use independently developed applied models or source-locked external
    problem definitions;
-   establish the benchmark question and selection criteria before
    results are known;
-   preserve source objectives, constraints, uncertainty, state, and
    decision structure;
-   hold the canonical PV-PP architecture fixed during execution;
-   avoid adding benchmark-specific operators merely to rescue a failed
    test;
-   distinguish benchmark defects, fixture or translation errors, search
    failures, policy failures, formalization gaps, scalar-reduction
    failures, and architecture failures; and
-   preserve unfavorable results, corrections, qualifications, and
    unresolved boundaries in the public record.

Benchmark objectives are not automatically PV-PP domains, and benchmark
results do not become canonical framework architecture merely because
they are publicly reported here.

## Current Real-World Benchmark Programs

### 01 MOEA RealWorldBenchmarks

The first completed real-world benchmark program uses applied problems
from the MOEA Framework **RealWorldBenchmarks** repository.

The exploratory tranche preselected three materially different cases:

-   Lower Rio Grande Valley water-supply portfolio planning;
-   lake-pollution control policy; and
-   general-aviation aircraft product-family design.

The three-case tranche is complete and frozen. Detailed selection
records, source reconstruction, execution artifacts, benchmark defects,
case results, synthesis, and interpretation limits are maintained inside
the `01 MOEA RealWorldBenchmarks` directory.

Future real-world benchmark families may be added alongside this program
when they test a genuinely different structural capability or provide a
materially different external evidence source.

## Relationship to the Public Benchmark Program

Real-World Benchmarks is one branch of the larger PV-PP public benchmark
record.

The current progression is:

1.  **AI Safety Gridworlds** --- independently designed safety
    mechanisms and failure modes.
2.  **MO-Gymnasium** --- standardized multi-objective environments and
    scalar-reduction boundaries.
3.  **Real-World Benchmarks** --- independently developed applied
    decision models.

The real-world category is intentionally broader than the current MOEA
tranche. The MOEA RealWorldBenchmarks program is the first source family
placed here; it is not the definition of the category itself.

## Authority Boundary

Materials in this directory are external tests and research evidence
concerning the PV-PP framework.

They do not define canonical PV-PP architecture.

Where a benchmark result identifies a possible architectural issue, that
result must pass through the framework's normal controlled research and
promotion process before it can affect canonical authority.

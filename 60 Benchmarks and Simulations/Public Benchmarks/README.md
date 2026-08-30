# Public Benchmark Program

This directory contains tests of the Productive Value-Productive Power
(PV-PP) framework against independently developed public benchmark
suites.

These benchmarks are distinct from the framework's internal numbered
simulation program. The benchmark problems were designed externally, the
PV-PP architecture was frozen during testing, and benchmark-specific
changes to the canonical architecture were not permitted simply to
rescue failed tests. Failures, limitations, source-fidelity
qualifications, fixture corrections, benchmark anomalies, and unresolved
issues are retained as part of the public benchmark record.

## Purpose

The purpose of the Public Benchmark Program is to test whether a frozen
PV-PP decision architecture can represent and execute decision problems
that were not designed around PV-PP.

The program is intended to provide externally anchored stress tests of
the framework rather than demonstrations constructed to confirm it. A
benchmark result may support the framework, expose a limitation,
identify an implementation or test-fixture problem, reveal a
benchmark-specific anomaly, or establish an unresolved formalization
boundary.

Passing a benchmark does not prove that PV-PP is generally correct,
optimal, safe, or superior to the benchmark's native methods.

## Benchmark Protocol

Public benchmark programs follow several general controls:

-   the benchmark source and relevant environment set are identified
    from public materials;
-   the PV-PP architecture being tested is frozen before benchmark
    execution;
-   the framework is not modified during execution merely to obtain a
    passing result;
-   failures and unfavorable results are preserved rather than removed
    from the record;
-   implementation errors and fixture corrections are documented
    separately from framework failures;
-   source-fidelity and dependency limitations are stated explicitly;
-   benchmark results are classified as evidence about the framework,
    not as additions to canonical framework authority; and
-   claims are limited to what the executed or source-audited tests
    actually establish.

## Public Record and Provenance

The directories below intentionally preserve the **substantive benchmark
record**, not only the final papers or favorable results.

Where available and relevant, the public record may include:

-   benchmark charters and frozen test specifications;
-   individual benchmark execution records;
-   test harnesses and analytical scripts;
-   machine-readable results and test outputs;
-   fixture corrections and implementation corrections;
-   source-fidelity and dependency notes;
-   failures, anomalies, and unresolved findings;
-   closeout and reconciliation records; and
-   final technical papers and research summaries.

This structure is deliberate. The final papers state the conclusions;
the numbered benchmark directories preserve the evidence and provenance
behind those conclusions.

Mechanical debris that does not contribute to the research record---such
as temporary Office files, caches, render intermediates, duplicate
disposable files, and operating-system artifacts---need not be retained.

## Completed Public Benchmark Programs

### 01 AI Safety Gridworlds

Testing of the frozen PV-PP decision architecture against every
individual environment listed in the archived AI Safety Gridworlds
repository, covering the safety-problem classes represented by that
suite.

The program examines problems including reward gaming, side effects,
unsafe exploration, absent supervision, distributional shift,
self-modification, interruptibility, and adversarial interaction.

The numbered `PB-001` through `PB-010` directories preserve the
individual benchmark record. `PB-000` contains summary, conclusion, and
publication-level materials.

### 02 MO-Gymnasium

Testing of the frozen PV-PP decision architecture against the complete
frozen MO-Gymnasium public multi-objective benchmark coverage set.

The program examines when scalar reduction is sufficient, when ordinary
linear weighted sums fail to recover decision-relevant alternatives, and
when adequacy, terminal state, reversibility, persistent state, or
multidimensional consequence structure should remain explicit.

The numbered `MB-001` through `MB-016` directories preserve the
benchmark execution record and tranche-level work. `MB-000` contains
summary, selection-audit, closeout, and publication-level materials.

## Relationship to Internal Simulations

The PV-PP research program also contains a larger internal numbered
simulation program. Those simulations were used during framework
development for exploratory, diagnostic, architectural, and
application-oriented work.

They are not part of this Public Benchmark Program and are not
reproduced here.

The distinction is deliberate:

-   **Internal simulations** are development and research instruments
    created within the PV-PP program.
-   **Public benchmarks** apply the framework to independently developed
    external benchmark suites under a frozen-architecture testing
    protocol.

This distinction should be preserved when citing or describing PV-PP
benchmark evidence.

## Authority Boundary

Public benchmark results are research evidence concerning the PV-PP
framework. They are not themselves canonical framework definitions.

No benchmark paper, result ledger, test harness, or benchmark-specific
interpretation supersedes the canonical framework documents. A benchmark
may identify evidence supporting a later controlled framework revision,
but that revision becomes authoritative only through the framework's
separate canonical promotion process.

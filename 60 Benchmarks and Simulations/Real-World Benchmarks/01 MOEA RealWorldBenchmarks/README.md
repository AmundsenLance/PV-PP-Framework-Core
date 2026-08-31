# PV-PP --- MOEA RealWorldBenchmarks Program

This directory contains the first completed real-world benchmark program
for the Productive Value-Productive Power (PV-PP) framework.

The program uses independently developed applied models from the MOEA
Framework **RealWorldBenchmarks** repository. It is one specific
benchmark family within the broader `Real-World Benchmarks` category.

## Source Repository and Freeze

The three cases in this exploratory tranche were selected from the MOEA
Framework **RealWorldBenchmarks** repository.

The supplied source repository was frozen for testing at Git commit:

`a4cc6312326df91dc92205b1aeac5721f83e1d36`

The benchmark source equations and decision structures were treated as
external authority. PV-PP was not permitted to redefine a source problem
merely to make it compatible with the framework.

## Benchmark Question

The governing question was:

> Can the frozen PV-PP architecture faithfully represent externally
> defined real-world constrained decisions while preserving the
> objectives, constraints, uncertainty, state structure, and
> decision-relevant distinctions of the original problem?

PV-PP was evaluated as a **decision architecture**, not as a replacement
optimization, search, control, or learning algorithm.

The three cases were selected before execution. The exploratory program
was also committed in advance to stop after the third case and assess
the evidence before considering expansion.

## Frozen Three-Case Tranche

### RWB-001 --- Water Supply Portfolio Planning

Lower Rio Grande Valley water-supply portfolio planning involving
permanent water rights, options contracts, leases, uncertainty, multiple
objectives, and hard reliability constraints.

**Primary result:** Adequacy / Constraint Distinction

The benchmark demonstrated that a lower-cost portfolio can remain
inadequate when externally defined reliability requirements fail.
Persistent supply capacity and transactional acquisition also remained
distinguishable.

A source implementation issue was discovered involving the Java
wrapper's calculation mode and the drought metrics declared by the
benchmark. The issue and its effect on results are preserved in the
benchmark record.

### RWB-002 --- Lake Pollution Control Policy

A 100-period nonlinear environmental policy problem involving persistent
lake state, anthropogenic phosphorus loading, stochastic natural inflow,
ecological threshold behavior, multiple objectives, and a hard
reliability floor.

**Primary result:** Adequacy / Constraint Distinction

The benchmark demonstrated that increased expected benefit cannot
compensate for crossing an externally defined ecological reliability
boundary. Temporal ordering and persistent environmental state also
remained decision-relevant.

A source implementation issue was discovered in the stochastic scenario
generator: repeated time-based reseeding can compromise the intended
independence of the nominal Monte Carlo samples. The supplied source was
not silently repaired.

### RWB-003 --- General Aviation Aircraft

A coupled product-family engineering problem involving three aircraft
variants, 27 design variables, 10 objectives, product-family
commonality, and 18 underlying engineering requirements.

**Primary result:** Multidimensional Preservation

The source aggregates 18 nonnegative engineering-requirement violations
into a single feasibility quantity. Because every component is
nonnegative, a total violation of zero is equivalent to all 18
requirements being satisfied.

For that specific binary feasibility question, **one scalar is enough**.

The same conclusion does not automatically apply to the benchmark's 10
performance objectives, which retain non-equivalent decision
information.

No implementation defect was identified in the executed GAA equations.

## Overall Result

All three preselected cases were executed without requiring a new
canonical PV-PP operator or state primitive.

The bounded conclusion is:

> Across three independently developed applied decision models with
> materially different structures, the frozen PV-PP architecture
> preserved the source problems' decision-relevant distinctions without
> requiring canonical architectural modification.

The cases collectively exercised:

-   uncertain resource portfolio planning;
-   persistent nonlinear environmental dynamics;
-   hard adequacy and reliability boundaries;
-   temporal and path-dependent consequences;
-   coupled multi-entity engineering design;
-   many-objective consequence structures;
-   product-family relational structure; and
-   both valid and invalid conditions for scalar reduction.

## Scalar Reduction Result

The MOEA real-world tranche reinforces a conditional view of scalar
reduction.

PV-PP does **not** assume that multidimensional representations are
always superior to scalar representations, and it does not assume that
every decision can safely be reduced to one number.

RWB-003 supplies an externally defined example of a lossless scalar
feasibility reduction. RWB-001 and RWB-002 demonstrate why compensatory
scalarization cannot automatically replace externally defined adequacy
or reliability boundaries.

The relevant question is whether the proposed reduction preserves every
distinction required for the decision being made.

## Source Fidelity and Benchmark Defects

The program uses source-locked execution wherever practical.

Implementation problems were discovered in two of the three external
benchmarks. These findings were preserved rather than corrected
silently.

The execution record distinguishes among:

-   benchmark implementation defects;
-   fixture or translation errors;
-   search failures;
-   policy failures;
-   scalar-reduction failures;
-   formalization gaps; and
-   architecture failures.

These categories are not interchangeable.

## Directory Structure

-   **RWB-000** --- program control, summaries, synthesis, and
    conclusions
-   **RWB-001** --- Lower Rio Grande Valley water-supply portfolio
    planning
-   **RWB-002** --- Lake pollution control policy
-   **RWB-003** --- General aviation aircraft product-family design

Each benchmark directory preserves the relevant source reconstruction,
execution records, results, qualifications, and closeout materials
available for that case.

## Program Status

**MOEA RealWorldBenchmarks exploratory tranche: COMPLETE / FROZEN**

-   RWB-001: CLOSED / PASS
-   RWB-002: CLOSED / PASS
-   RWB-003: CLOSED / PASS
-   Canonical PV-PP architecture changes required: **NONE**

The three-case stopping point was established before completion rather
than chosen after observing favorable results.

Expansion to additional problems in the source repository is not
automatic. A future case should be selected only when it tests a
structural capability not already adequately exercised by the completed
tranche.

## Interpretation Limits

These results do not establish that PV-PP:

-   is an optimal search or learning algorithm;
-   outperforms multi-objective evolutionary algorithms, operations
    research, control theory, or domain-specific optimization;
-   has been proven adequate for every real-world decision problem;
-   reconstructed the global Pareto frontiers of these problems; or
-   can safely scalarize every multidimensional decision.

The results are constructive evidence about representational
compatibility, adequacy preservation, multidimensional structure, and
conditional scalar reduction under a frozen architecture.

## Relationship to the Parent Category

This directory documents one source family within the broader PV-PP
`Real-World Benchmarks` category.

The parent category is intended to accommodate other independently
developed real-world benchmark families in the future when they add
genuinely new evidence. The completion of this MOEA tranche therefore
closes this program, not the possibility of future real-world benchmark
research from other external sources.

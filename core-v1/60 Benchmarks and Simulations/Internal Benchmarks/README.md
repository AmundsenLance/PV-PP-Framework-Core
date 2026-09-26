# PV-PP Internal Benchmarks

This directory contains internally constructed benchmark environments
used to stress the Productive Value-Productive Power (PV-PP) framework
under controlled conditions.

Internal benchmarks differ from the standardized environments in
`Public Benchmarks` and the independently developed applied models in
`Real-World Benchmarks`. They are deliberately designed to combine
framework-relevant structures that may not coexist in available external
benchmark suites.

Their purpose is not to create favorable demonstrations. Their value
depends on prospective specification, frozen architecture, controlled
comparison, preserved failures and corrections, and reproducible
execution.

## Purpose

The governing question for this category is:

> Can the frozen PV-PP architecture maintain coherent decision behavior
> when multiple productive-system mechanisms interact dynamically under
> uncertainty?

Depending on the benchmark, those mechanisms may include:

-   heterogeneous economic agents;
-   persistent productive capacity;
-   productive-value exchange;
-   resource and capacity dependencies;
-   contractual or productive commitments;
-   incomplete or imperfect information;
-   financing and liquidity constraints;
-   quality and reliability deterioration;
-   recovery pathways and adaptation;
-   delayed consequences;
-   irreversible losses or collapse; and
-   multi-period interaction among agents whose decisions alter one
    another's future productive states.

PV-PP is evaluated as a **decision architecture**. Internal benchmark
environments, fixtures, parameters, and outcomes do not themselves
become canonical PV-PP architecture.

## Current Internal Benchmark Program

### Asterion Benchmark

The current principal internal benchmark is **Asterion Benchmark V2**,
an integrated stochastic multi-agent productive-system stress benchmark.

Asterion contains a manufacturer, suppliers, a customer, a lender,
logistics, inventories, contracts, financing constraints, quality
processes, supplier deterioration and recovery, alternate productive
capacity, delayed field consequences, incomplete information, and
productive-power states that can deteriorate or recover over time.

The benchmark compares the frozen PV-PP controller architecture with a
specified family of scalar receding-horizon controllers and a local
deterministic priority controller under common stochastic worlds.

The final banked M14 ensemble contains:

-   **1,000 common stochastic seeds**;
-   **7 decision regimes**; and
-   **7,000 completed production runs**.

The Asterion directory contains the benchmark-definition materials,
final M14 execution package, banking and validation records, and
publication white paper.

See `Asterion Benchmark/README.md` for benchmark-specific details.

## Research Discipline

Internal benchmarks should follow several general rules:

-   establish the benchmark architecture and research question before
    production results are interpreted;
-   distinguish canonical PV-PP architecture from benchmark-world rules
    and fixtures;
-   freeze the tested controller architecture before the production
    ensemble;
-   define comparison controllers independently of observed production
    outcomes;
-   preserve common random numbers or equivalent controlled comparison
    structures where applicable;
-   do not add benchmark-specific PV-PP operators merely to rescue a
    failed test;
-   preserve material implementation defects, diagnostic runs,
    corrections, and supersessions when necessary to understand the
    evidentiary lineage;
-   distinguish benchmark defects, implementation defects, search
    failures, comparator behavior, formalization gaps, and genuine
    architecture failures; and
-   report heterogeneous outcomes in their native dimensions rather than
    manufacturing a universal benchmark score without independent
    justification.

An internally designed benchmark carries an unavoidable risk of designer
advantage. For that reason, specification control, comparator quality,
prospective correction, reproducibility, and preservation of unfavorable
evidence are especially important in this category.

## Relationship to Other Benchmark Categories

The PV-PP benchmark record currently contains three complementary
branches:

1.  **Internal Benchmarks** --- constructed stress environments designed
    to exercise interacting portions of the framework.
2.  **Public Benchmarks** --- standardized external environments such as
    AI Safety Gridworlds and MO-Gymnasium.
3.  **Real-World Benchmarks** --- independently developed applied
    decision models.

Internal benchmarks provide control and architectural coverage. Public
and real-world benchmarks provide external problem structure that was
not designed around PV-PP.

Evidence from these categories should therefore be considered together
rather than treating any one benchmark family as sufficient by itself.

## Authority Boundary

Materials in this directory are benchmark definitions, execution
artifacts, validation records, and research evidence concerning the
PV-PP framework.

They do **not** define canonical PV-PP architecture.

A benchmark result that suggests an architectural change must pass
through the framework's normal controlled research, review, and
promotion process before it can alter canonical authority.

## Repository Scope

This public directory is a curated research record, not a complete copy
of the internal development workspace.

For each internal benchmark, the repository should preserve the
materials necessary to:

-   understand what was tested;
-   identify the frozen benchmark and controller definitions;
-   reproduce or inspect the execution;
-   verify the production results;
-   understand material corrections or supersessions; and
-   interpret the resulting evidence within its stated limits.

Redundant temporary files, routine intermediate builds, editor
artifacts, caches, and developmental scratch material need not be
included when they add no evidentiary or reproducibility value.

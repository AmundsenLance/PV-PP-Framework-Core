# AI Safety Gridworlds --- PV-PP Public Benchmark Program

This directory contains the public research record for testing the
Productive Value-Productive Power (PV-PP) framework against the archived
**AI Safety Gridworlds** environment set developed by researchers at
DeepMind.

AI Safety Gridworlds provides deliberately small reinforcement-learning
environments designed to make recurring AI-safety problems concrete and
testable. The PV-PP program used the suite as an external architectural
stress test. The objective was not to compare reinforcement-learning
scores or claim that PV-PP is an AI-safety solution. The question was
whether a frozen PV-PP decision architecture could represent and execute
the central decision problem in each repository-listed environment
without adding a benchmark-specific canonical operator after seeing the
test.

## Coverage

The program exercised every individual environment listed in the
archived AI Safety Gridworlds repository:

-   Safe Interruptibility
-   Side Effects Sokoban
-   Conveyor Belt
-   Absent Supervisor
-   Boat Race
-   Tomato Watering
-   Whisky & Gold
-   Distributional Shift
-   Friend or Foe
-   Island Navigation

These ten repository-listed environments cover the eight safety-problem
classes represented by the suite.

Conveyor Belt is included because it is listed in the archived
repository. It should not be described as one of ten environments
appearing in the original 2017 AI Safety Gridworlds paper; its
repository source points to later side-effects work.

## Benchmark Protocol

The canonical PV-PP architecture was held fixed during the benchmark
program. Benchmark-specific changes to the architecture were not
permitted simply to obtain passing results.

The tests preserve distinctions among:

-   failure caused by incomplete task specification;
-   failure of a candidate policy;
-   implementation or fixture error;
-   source-fidelity limitation;
-   benchmark-specific anomaly or exploit;
-   unresolved PV-PP formalization boundary; and
-   genuine architectural failure.

Several tests were controlled mechanism translations rather than full
reinforcement-learning training reproductions. Those fidelity
limitations remain part of the public result.

## Overall Result

All ten repository-listed AI Safety Gridworlds environments were
exercised against PV-PP, covering all eight safety-problem classes
represented by the suite, and **none of the ten required a new canonical
PV-PP operator or state primitive to represent and execute its central
decision problem**.

That result is constructive evidence, not proof.

The benchmark program does **not** establish that:

-   PV-PP "beat" AI Safety Gridworlds;
-   PV-PP is generally safe;
-   PV-PP is superior to reinforcement learning or other AI-safety
    methods;
-   every test was a full reproduction of the original training
    environment; or
-   the PV-PP architecture has no unresolved formalization issues.

## Important Qualifications

The benchmark record deliberately retains unfavorable and limiting
results.

**Side Effects Sokoban** showed that an incompletely framed task can
still produce the harmful shortcut. PV-PP did not manufacture a
preservation objective that had not been specified.

**Distributional Shift** and **Safe Interruptibility** were tested
through controlled mechanism-level translations rather than fully
matched reproductions of the original environments and training
processes. Their source-fidelity qualifications remain attached to the
results.

**Whisky & Gold** required a fixture correction after the initial
random-motion implementation was found to bias the result. The
correction changed the fixture rather than PV-PP policy logic.

**Friend or Foe** exposed a benchmark-mechanism exploit: a deterministic
alternating strategy performed unexpectedly well because the
source-derived adversary's estimator lagged the sequence. That result
was recorded as an exploit of the benchmark mechanism, not as evidence
of general adversarial robustness.

## Derived Adversarial Hardening Test

The Friend-or-Foe anomaly motivated a separate derived hardening test,
PB-009H.

In that construction, the adversary was assumed to know the agent's
deterministic rule and relevant history. Deterministic strategies could
therefore be predicted and defeated. A genuinely mixed 50/50 policy
produced a theoretical maximin success rate of 0.5 and approximately
0.4943 in simulation.

PB-009H is **not an official AI Safety Gridworlds environment** and is
not counted among the ten repository-listed environments.

It exposed an unresolved PV-PP formalization boundary concerning
deliberate randomized policies: the existing architecture is broad
enough to describe policies as rules and to select a policy
deterministically, but the canonical specification does not yet
explicitly formalize probability-bearing policy objects,
distribution-valued projected consequences, and private randomized
realization.

The framework was not patched during the benchmark program. The issue
remains a formalization boundary for separate controlled review.

## Recurring Architectural Findings

Across the suite, the same PV-PP distinctions repeatedly proved useful:

-   actual state versus perceived or reported state;
-   task structure versus visible reward;
-   feasibility and safety constraints versus preference among feasible
    alternatives;
-   selected policy versus realized execution;
-   context- and counterparty-specific information versus universalized
    behavior;
-   exogenous environmental transition versus agent-caused interference;
    and
-   deterministic policy selection versus the still-open representation
    of deliberate mixed execution.

The significance of the result is not that one special PV-PP rule solved
ten environments. It is that independently designed problems repeatedly
mapped onto distinctions that were already present in the frozen
architecture.

## Directory Structure and Public Record

This directory intentionally preserves the substantive benchmark
history.

-   `PB-000` contains summary, conclusion, closeout, and
    publication-level materials.
-   `PB-001` through `PB-010` contain the individual AI Safety
    Gridworlds benchmark records.
-   Benchmark directories may contain charters, execution records, test
    harnesses, code, result files, corrections, source-fidelity notes,
    and other substantive artifacts needed to understand how a reported
    result was obtained.

Failures, fixture corrections, anomalies, and qualified results are
retained because they are part of the evidence. The repository is
intended to make the path from published conclusion to underlying
benchmark record inspectable.

Mechanical debris that does not contribute to provenance or
reproducibility need not be retained.

## Source Benchmark

Original paper:

Jan Leike, Miljan Martic, Victoria Krakovna, Pedro A. Ortega, Tom
Everitt, Andrew Lefrancq, Laurent Orseau, and Shane Legg. **AI Safety
Gridworlds.** arXiv:1711.09883 (2017).

Archived source repository:

https://github.com/google-deepmind/ai-safety-gridworlds

## Authority Boundary

These benchmark results are research evidence concerning the Productive
Value-Productive Power framework. They are not canonical PV-PP
definitions and do not supersede canonical framework documents.

A benchmark finding may motivate a later controlled clarification or
revision, but benchmark-specific analysis becomes part of canonical
PV-PP authority only through the framework's separate promotion and
authority process.

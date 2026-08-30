# MO-Gymnasium --- PV-PP Public Benchmark Program

This directory contains the public research record for testing the
Productive Value-Productive Power (PV-PP) framework against
**MO-Gymnasium**, the public multi-objective reinforcement-learning
benchmark library maintained by the Farama Foundation.

MO-Gymnasium exposes vector-valued rewards rather than requiring every
decision problem to be reduced immediately to a single reward scalar.
That made the suite a useful external test of a central PV-PP question:
**when is one number enough?**

The benchmark program did not ask whether PV-PP could outperform trained
multi-objective reinforcement-learning agents. It asked whether a frozen
PV-PP decision architecture could preserve the decision-relevant
structure of the benchmark problems, recognize cases where scalar
reduction was sufficient, and distinguish cases where reduction
discarded information relevant to feasibility, adequacy, terminal state,
reversibility, or efficient alternatives.

## Coverage

The final program was reconciled against the frozen **MO-Gymnasium
v1.3.2** public registration set used for this benchmark.

The coverage set contains **31 registrations** across four groups:

### Grid-World --- 8 registrations

-   `deep-sea-treasure-v0`
-   `deep-sea-treasure-concave-v0`
-   `deep-sea-treasure-mirrored-v0`
-   `resource-gathering-v0`
-   `fishwood-v0`
-   `breakable-bottles-v0`
-   `fruit-tree-v0`
-   `four-room-v0`

### Classic Control --- 7 registrations

-   `mo-mountaincar-v0`
-   `mo-mountaincar-3d-v0`
-   `mo-mountaincar-timemove-v0`
-   `mo-mountaincar-timespeed-v0`
-   `mo-mountaincarcontinuous-v0`
-   `mo-lunar-lander-v3`
-   `mo-lunar-lander-continuous-v3`

### Miscellaneous --- 7 registrations

-   `water-reservoir-v0`
-   `minecart-v0`
-   `minecart-rgb-v0`
-   `minecart-deterministic-v0`
-   `mo-highway-v0`
-   `mo-highway-fast-v0`
-   `mo-supermario-v0`

### MuJoCo --- 9 registrations

-   `mo-reacher-v5`
-   `mo-hopper-v5`
-   `mo-hopper-2obj-v5`
-   `mo-halfcheetah-v5`
-   `mo-walker2d-v5`
-   `mo-ant-v5`
-   `mo-ant-2obj-v5`
-   `mo-swimmer-v5`
-   `mo-humanoid-v5`

Current source registrations and environment-specific documentation were
used during reconciliation where older aggregate documentation retained
superseded registration names.

## Benchmark Protocol

The program began with three primary tests selected before their PV-PP
outcomes were known:

1.  **MountainCar** --- scalar-containment baseline;
2.  **Minecart** --- Pareto and resource-tradeoff test; and
3.  **Water Reservoir** --- threshold, adequacy, and infeasibility
    stress test.

Fruit Tree was identified as a reserve case.

After those initial tests, the program was deliberately expanded to
complete-suite coverage to remove a reasonable selection-bias objection.
The expansion was frozen before the remaining results were known.

The governing controls were:

-   the canonical PV-PP architecture remained fixed during execution;
-   no benchmark-specific canonical change could be made simply to
    obtain a passing result;
-   every registration in the frozen coverage set required a recorded
    disposition;
-   materially different objective or reward variants were executed or
    separately analyzed;
-   structurally equivalent or observation-only variants could be
    equivalence-covered with an explicit rationale;
-   failures, unfavorable findings, fixture corrections, dependency
    limitations, and formalization gaps remained in the ledger; and
-   claims were limited to the execution or source-audit method actually
    used.

## Overall Result

All **31 registrations** in the frozen MO-Gymnasium v1.3.2 coverage set
were exercised or explicitly equivalence-covered.

**None required a new canonical PV-PP operator or state primitive.**

The most important result, however, is not a 31-of-31 score. The suite
produced evidence on both sides of the scalar-reduction question.

Some environments were clean cases in which a stable scalar reduction
was sufficient.

Other environments showed that ordinary fixed nonnegative linear
weighted sums did not recover every efficient alternative, that a scalar
optimum could exist even when the explicitly framed adequate set was
empty, or that terminal state, reversibility, event history, and task
semantics carried information that should not automatically be treated
as another compensable reward component.

The benchmark-supported conclusion is therefore conditional:

> **Scalarization is sometimes enough. Multidimensional structure should
> remain explicit until the decision architecture can establish that
> reduction is safe.**

## Major Findings

### Scalar containment

Several environments provided positive evidence for scalar reduction.

**MountainCar** showed that a stable scalar map can reproduce the
relevant policy selection under appropriate task semantics.

**Fruit Tree** provided a strong high-dimensional control. In the
complete depth-5 leaf set, all 32 terminal outcomes were
Pareto-efficient and all 32 were uniquely supportable by some
nonnegative linear weighting.

Much of the **MuJoCo** tranche also supplied direct scalar-containment
evidence. Hopper, HalfCheetah, Walker2D, Swimmer, and Humanoid expose
reward components that can be recombined through documented linear
weights to recover their original Gymnasium scalar rewards.

These cases are important because the PV-PP benchmark position is not
"vectors good, scalars bad."

### Pareto-efficient alternatives not recovered by ordinary linear weighted sums

**Minecart** produced 10 Pareto-efficient return vectors in the
source-derived analytical test. Only 6 were supported by any tested
nonnegative linear weighting; 4 efficient points were unsupported.

The separately registered deterministic Minecart variant changed the
numerical frontier but reproduced the same 6-supported / 4-unsupported
structure.

**Deep Sea Treasure** supplied an internal control. On the standard
frontier, all 10 Pareto points were linearly supported. On the concave
and mirrored frontiers, only the two endpoints were supported and 8 of
10 interior Pareto-efficient points were unsupported.

**Continuous MountainCar** produced a similar result within a frozen
candidate-policy family. Among 46 nondominated successful candidates, 15
were supported by a fixed nonnegative linear weighting and 31 were
unsupported. This finding is limited to the tested candidate family and
is not a claim about the global environment Pareto frontier.

These findings concern ordinary fixed nonnegative weighted sums over the
stated objective vectors. They do not establish that no nonlinear,
constrained, lexicographic, state-conditioned, or other scalar
representation could recover the same decisions.

### Adequacy versus maximization

**Water Reservoir** produced the clearest infeasibility distinction. In
the four-objective stress configuration, one zero-deficit requirement
required release of at least 50 units while another required release of
no more than 30. The strict jointly adequate set was therefore empty.

A scalar optimizer still returned a maximizing compromise.

PV-PP preserved the distinction between:

-   "this is the highest-ranked compromise under the chosen scalar"; and
-   "this policy satisfies the framed requirements."

**Fishwood** showed a related but less severe case. A joint
fish-and-wood requirement could uniquely identify an interior adequate
allocation even when ordinary linear weighting selected an endpoint or
became indifferent across allocations. A task-specific nonlinear scalar
could also recover the balanced solution.

### Terminal state, reversibility, and persistent evidence

**Breakable Bottles** distinguished expected efficiency from policies
containing an irreversible-loss branch.

**Four Room** showed that terminal reward is not necessarily equivalent
to evidence that required events occurred: the goal can grant `[1,1,1]`
even when the relevant item-collection history differs.

**Lunar Lander** uses regime-dependent source reward semantics.
Nonterminal shaping and fuel terms can be linearly recombined, while
terminal landing or crash overwrites the legacy scalar even though the
vector retains shaping and fuel components. One fixed linear weighting
cannot exactly reproduce both arbitrary regimes.

**Highway** and **Super Mario** both illustrate that terminal failure
can be represented as a finite reward component and therefore
mathematically compensated by enough positive reward under some weights.
If collision-free travel or reaching the flag alive is part of the
framed task, terminal survival can instead be represented as an adequacy
or admissibility condition before ordinary benefit ranking.

## Execution and Fidelity Boundary

This program is a decision-representation and structural benchmark, not
a 31-environment reinforcement-learning tournament.

The benchmark methods included:

-   exact enumeration;
-   source-derived analytical Pareto calculations;
-   deterministic mechanism tests;
-   Monte Carlo probes;
-   frozen candidate-policy-family analysis;
-   source-faithful reward and transition audits; and
-   explicitly justified equivalence coverage.

Several dependency-heavy environments could not be executed as full
installed simulator stacks in the benchmark execution environment. In
those cases, the public record identifies the result as a
source-faithful mechanism or reward-structure audit rather than a
trained-agent or full-physics reproduction.

Accordingly, **complete-suite coverage does not mean 31 trained-agent
reproductions**.

## What the Result Does Not Establish

The completed benchmark program does not establish that:

-   PV-PP is superior to multi-objective reinforcement learning;
-   PV-PP is an optimal decision system;
-   scalar representations are generally inadequate;
-   vector representations are generally superior;
-   every MO-Gymnasium policy frontier was exhaustively characterized;
-   every environment was executed through a fully installed native
    simulator; or
-   the PV-PP architecture is universally complete.

MO-Gymnasium itself supports methods far richer than a fixed linear
weighted sum. The benchmark results should not be restated as a general
criticism of MORL.

## Directory Structure and Public Record

This directory intentionally preserves the substantive MO-Gymnasium
benchmark history.

-   `MB-000` contains summary, selection-audit, closeout, and
    publication-level materials.
-   `MB-001` through `MB-015` contain the individual benchmark-family
    records.
-   `MB-016` contains the final MuJoCo tranche and suite-completion
    work.
-   Individual directories may contain charters, source notes,
    analytical programs, test harnesses, machine-readable results,
    regression outputs, corrections, closeouts, and other substantive
    benchmark artifacts.

The inclusion of intermediate benchmark stages is deliberate where those
stages contribute to provenance, reproducibility, or interpretation.
Unfavorable findings, fixture corrections, dependency limitations, and
source-fidelity qualifications are part of the public record rather than
material to be removed after closeout.

Mechanical debris that does not contribute to the research record need
not be retained.

## Source Benchmark

MO-Gymnasium documentation:

https://mo-gymnasium.farama.org/

MO-Gymnasium source repository:

https://github.com/Farama-Foundation/MO-Gymnasium

Primary benchmark reference:

Florian Felten, Lucas N. Alegre, Ann Nowé, Ana L. C. Bazzan, El-Ghazali
Talbi, Grégoire Danoy, and Bruno C. da Silva. **A Toolkit for Reliable
Benchmarking and Research in Multi-Objective Reinforcement Learning.**
Advances in Neural Information Processing Systems 36 (2023).

## Authority Boundary

These benchmark results are research evidence concerning the Productive
Value-Productive Power framework. They are not canonical PV-PP
definitions and do not supersede canonical framework documents.

A benchmark result may support a later controlled framework
clarification or revision, but benchmark-specific analysis becomes part
of canonical PV-PP authority only through the framework's separate
promotion and authority process.

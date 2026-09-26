# Asterion Benchmark V2

Asterion Benchmark V2 is an internally constructed stochastic
multi-agent productive-system benchmark for the Productive
Value-Productive Power (PV-PP) framework.

It was designed to stress a large portion of the frozen PV-PP decision
architecture simultaneously rather than testing another isolated
operator or another static multi-objective choice.

## Governing Research Question

The benchmark asks:

> Can the frozen PV-PP architecture maintain coherent decision behavior
> in a dynamic multi-agent productive system containing heterogeneous
> agents, persistent productive capacity, productive-value exchange,
> resource dependencies, contractual or productive commitments,
> incomplete information, delayed consequences, recovery pathways, and
> irreversible productive losses?

The benchmark is a controlled test of decision architectures inside a
specified productive system. It is not a claim that Asterion reproduces
an entire real economy.

## Productive System

The Asterion world includes interacting economic roles representing:

-   a manufacturer (`M`);
-   a primary supplier (`S1`);
-   an alternate supplier (`S2`);
-   a customer (`C`);
-   a lender (`L`);
-   a transportation/logistics provider (`T`); and
-   a regulatory/certification function (`R`).

The environment contains inventories, production capacities, cash and
credit, contracts and commitments, supplier qualification, logistics,
inspection, latent defects, field-quality consequences,
productive-capability deterioration and recovery, customer reserves, and
downstream operational productive power.

Agents operate with incomplete information. Hidden realized state is not
supplied to controllers as an oracle.

## Decision Regimes

The final M14 benchmark compares seven regimes.

### A --- PV-PP

Regime A uses the frozen PV-PP architecture.

Candidate actions are generated through the common action grammar and
evaluated through the framework's ordered decision structure, including
constraints, domain framing, adequacy, productive-power consequences,
recovery structure, and the frozen selection operator.

The architecture does not reduce all decision-relevant consequences to a
single universal scalar score.

### B0-B4 --- Scalar Receding-Horizon Comparators

B0 is the balanced scalar comparator.

It uses the same public world model, planning horizon, action interface,
and non-oracular information boundary as A. Role-native outcome
dimensions are normalized and combined into a frozen weighted loss
function using:

-   75% expected normalized horizon loss; and
-   25% CVaR at the 90% level.

B1-B4 are prospectively frozen sensitivity variants emphasizing:

-   continuity;
-   resilience;
-   financial conservatism; and
-   quality/safety.

These variants test whether the principal comparison depends on one
particular scalar weighting choice.

### C --- Local Deterministic Priority Comparator

Regime C uses a deterministic current-state priority architecture with a
frozen four-period recent-history window.

It responds to current productive, safety, quality, financial,
contractual, and reliability conditions but does not explicitly optimize
a multi-period recovery corridor.

## Final Banked Run: M14

M14 is the clean primary Asterion Benchmark V2 evidence set.

The final production ensemble contains:

-   **1,000 common stochastic seeds**;
-   **7 regimes per seed**;
-   **7,000 complete regime-runs**;
-   **0 production failures**; and
-   **0 structural validation errors**.

The production run passed the benchmark's conformance, readiness,
structural-validation, action-surface-parity, and post-run integrity
checks.

The M14 production results are **banked as primary evidence**.

## Benchmark Lineage

The public interpretation of M14 depends on a controlled development
lineage.

### M12

M12 was the first banked hard Asterion benchmark and remains historical
evidence.

### M13

M13 prospectively changed the customer-exit semantics so that customer
distress indicators did not automatically terminate the customer while
customer operational productive power remained above zero.

After production, audit identified a quality-path implementation defect:
the major field-quality trigger was evaluated against failures processed
in the current due period rather than the frozen rolling delivered
cohort.

M13 was therefore preserved as **diagnostic and unbanked** evidence.

### M14

M14 repaired that implementation defect and associated
quality-path/provenance issues from frozen authority or outcome-blind
prospective closure. The M13 customer-exit change was retained
unchanged.

M14 then passed the expanded conformance and readiness suite before a
new production ensemble was executed.

This lineage is important because M14 is not a retrospective selection
of favorable M13 outcomes. The material corrections were made
prospectively from benchmark authority before the clean M14 ensemble was
run.

## Headline M14 Results

Against the principal balanced scalar comparator B0, the paired
1,000-seed M14 ensemble produced the following mean A-minus-B0
differences:

  Outcome                               Mean A-B0
  --------------------------------- -------------
  Delivered usable units                 +185.627
  Physical shortage unit-weeks           -178.361
  Terminal manufacturer cash          +\$380.620k
  Adaptation expenditure               -\$71.340k
  Terminal S1 line PP                     +34.810
  Terminal S1 quality PP                  +45.138
  Major field-quality events               -0.688
  Terminal customer operations PP         +11.160

Directionality was also strong. A delivered more usable product in **999
of 1,000** common seeds and preserved greater terminal S1 line and
quality PP in **1,000 of 1,000** seeds.

These results are benchmark-relative. They do not establish universal
superiority of PV-PP over scalar optimization or other decision
architectures.

Rare customer-collapse outcomes are reported descriptively. Their event
rate is too low in this ensemble to support the same strength of
inferential conclusion as the continuous productive-system outcomes.

## Statistical Analysis

Publication-facing statistical analysis uses the frozen native-unit
reporting contract.

The analysis includes:

-   means, sample standard deviations, medians, interquartile-range
    components, and predeclared 10th/90th percentiles;
-   paired A-versus-comparator seed differences;
-   10,000-resample paired bootstrap percentile confidence intervals;
-   secondary Wilcoxon signed-rank tests;
-   Holm multiplicity adjustment within predeclared outcome families;
-   matched binary contingency tables and exact McNemar tests where
    applicable; and
-   deterministic script-level anonymous regime labels during validity
    and outcome aggregation.

No universal benchmark score is constructed.

## Directory Contents

The public Asterion directory is intentionally compact.

### `Initial Benchmark Definition Documents`

Contains the benchmark-definition and authority materials needed to
understand what was prospectively specified and frozen.

### `pvpp_m14_build_FINAL_RUN`

Contains the final M14 execution package and production evidence used
for the banked run.

This is the authoritative final-run package rather than a collection of
every developmental build.

### `M14_Banking_and_Validation_Record_v1_FINAL_RUN.docx`

Records the final production validation, integrity checks, principal
results, and formal banking decision.

### `M14_Pre_Banking_Quality_Path_Audit_Record_v1_FINAL_RUN.docx`

Records the pre-banking quality-path audit and the prospective D10
repair lineage leading to the clean M14 run.

### `PV-PP_Asterion_Benchmark_V2_Publication_WHITE_PAPER_v0_6.docx`

Publication-facing benchmark paper describing the Asterion system,
controller architectures, experimental design, validation, statistical
results, trace-supported interpretation, limitations, and
reproducibility record.

## Reproducibility

The final-run materials preserve the frozen benchmark configuration,
source code, seed set, tests, production outputs, validation records,
and statistical evidence needed to inspect the M14 benchmark.

The 1,000 seeds are common across regimes so paired comparisons evaluate
different decision architectures against corresponding stochastic
worlds.

Where stochastic events represent the same underlying physical event
across regimes, the benchmark uses event-keyed common-random-number
semantics so controller identity does not itself change the random draw.

The repository intentionally excludes routine temporary files and
redundant developmental builds that are not necessary to reproduce or
audit the banked result.

## Interpretation Boundary

M14 provides strong evidence about behavior **within the frozen Asterion
benchmark**.

It does not prove:

-   that PV-PP is universally optimal;
-   that every scalar controller must behave like B0-B4;
-   that no alternative scalar or non-scalar architecture could
    reproduce similar behavior;
-   that productive-power preservation guarantees recovery under every
    stochastic realization; or
-   that results from this constructed productive system automatically
    generalize to real economies.

The supported conclusion is narrower:

> In the frozen Asterion stochastic multi-agent productive-system
> benchmark, the PV-PP controller architecture produced substantially
> stronger productive-system outcomes than the specified comparison
> controllers across a 1,000-seed common-random-number ensemble, while
> preserving more productive capacity and requiring less adaptation
> expenditure than the principal balanced scalar comparator.

## Authority Boundary

Asterion is benchmark evidence concerning PV-PP. It is not canonical
PV-PP architecture.

Benchmark-specific world rules, parameters, fixtures, comparator
definitions, and empirical outcomes do not become framework authority
merely because they appear in the public benchmark record.

Any architectural issue identified by Asterion must pass through the
PV-PP project's normal controlled research and promotion process before
it can alter canonical framework authority.

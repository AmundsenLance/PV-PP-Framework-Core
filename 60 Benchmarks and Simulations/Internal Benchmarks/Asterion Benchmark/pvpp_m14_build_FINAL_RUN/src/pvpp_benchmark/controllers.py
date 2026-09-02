from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable
from .model import *

@dataclass
class ScalarBelief:
    value: float
    uncertainty: float

@dataclass
class ScalarEstimator:
    beliefs: dict[str, ScalarBelief]=field(default_factory=dict)
    reliability_alpha_beta: dict[str, list[float]]=field(default_factory=dict)

    def source_reliability(self, source: str) -> float:
        a,b=self.reliability_alpha_beta.setdefault(source,[2.0,2.0])
        return a/(a+b)

    def update_checkable_source(self, source: str, correct: bool):
        ab=self.reliability_alpha_beta.setdefault(source,[2.0,2.0])
        ab[0 if correct else 1]+=1

    def absorb(self, packet: Packet):
        if packet.kind is not PacketKind.PRE:
            raise ValueError("scalar estimator accepts PRE only")
        for e in packet.evidence:
            if e.claim_family=="supplier_status" and e.source==Role.S1 and e.payload.get("mode")=="exact":
                rel=self.source_reliability("S1")
                for k in ("line","quality"):
                    if k in e.payload:
                        old=self.beliefs.get(f"S1.{k}")
                        observed=float(e.payload[k])
                        if old is None:
                            self.beliefs[f"S1.{k}"]=ScalarBelief(observed,15*(1-rel)+2)
                        else:
                            w=max(.2,rel)
                            old.value=w*observed+(1-w)*old.value
                            old.uncertainty=max(2.0,old.uncertainty*.85)

    def propagate_freshness(self, periods: int=1):
        for b in self.beliefs.values():
            b.uncertainty=min(100,b.uncertainty+3*periods)

@dataclass(frozen=True)
class Candidate:
    policy_id: str
    valid: bool
    adequate: bool
    governing_vector: tuple[float,...]
    all_domain_vector: tuple[float,...]
    irreversible_critical_damage: bool=False

class SigmaSelector:
    """Conformance implementation of the frozen three-mode Sigma contract.

    Lower numeric loss/collapse components are better. This module does not determine
    validity or adequacy and does not repair candidates.
    """
    @staticmethod
    def _pareto(cands: list[Candidate], attr: str) -> list[Candidate]:
        out=[]
        for c in cands:
            v=getattr(c,attr)
            dominated=False
            for d in cands:
                if d is c: continue
                w=getattr(d,attr)
                if all(x<=y for x,y in zip(w,v)) and any(x<y for x,y in zip(w,v)):
                    dominated=True; break
            if not dominated: out.append(c)
        return out

    def select(self, candidates: Iterable[Candidate]) -> Candidate | None:
        c=list(candidates)
        adequate=[x for x in c if x.valid and x.adequate]
        if adequate:
            p=self._pareto(adequate,"governing_vector")
            p=self._pareto(p,"all_domain_vector")
            return sorted(p,key=lambda x:x.policy_id)[0]
        valid=[x for x in c if x.valid]
        if valid:
            # Recovery-unavailable fallback: lexicographic governing collapse.
            ordered=sorted(valid,key=lambda x:(x.governing_vector,x.policy_id))
            winner=ordered[0]
            # Frozen bounded structural override: only a one-period marginal first-difference.
            for alt in ordered[1:]:
                if not winner.irreversible_critical_damage or alt.irreversible_critical_damage:
                    continue
                diffs=[(i,a,b) for i,(a,b) in enumerate(zip(winner.governing_vector,alt.governing_vector)) if a!=b]
                if diffs:
                    _,a,b=diffs[0]
                    if b-a <= 1:
                        winner=alt; break
            return winner
        return None

LOCAL_PRIORITIES={
    Role.M:("safety","delivery","cash","quality","cost","reliability","reversibility","encumbrance"),
    Role.S1:("safety","shipment","cash","capability","cost","reliability","reversibility"),
    Role.S2:("qualification","contract","cash","capability","external_opportunity","cost","reversibility"),
    Role.C:("continuity","quality","reserve","contract","switching_cost","reliability","reversibility"),
    Role.L:("legal","credit_loss","covenant","workout","return","amendment_cost"),
    Role.T:("physical","reserved_capacity","service","overload","cost","reliability"),
}

BASE_B_WEIGHTS={
    Role.M:{"commitment":1,"shortage":1,"cash":1,"capability":1,"quality":1,"adaptation":.75,"recovery":1.25},
    Role.S1:{"fulfillment":1,"cash":1,"line":1,"quality":1.1,"recovery_cost":.75,"exit":1.35},
    Role.S2:{"qualification":1,"cash":1,"opportunity":1,"quality":1.1,"adaptation":.75,"market_loss":1.15},
    Role.C:{"shortage":1.25,"reserve":1.15,"operations":1.25,"quality":1.25,"contract":.8,"switching":.6},
    Role.L:{"credit_loss":1.4,"covenant":1.2,"liquidity":1,"workout":.6,"return":.5,"continuity":.7},
    Role.T:{"reservation":1.2,"overload":1,"service":1.2,"expedite":.7,"cost":.7,"reliability":1},
}

# Production decision classes are imported lazily from planning.py to keep the
# foundational data structures independent of the calibration projector.

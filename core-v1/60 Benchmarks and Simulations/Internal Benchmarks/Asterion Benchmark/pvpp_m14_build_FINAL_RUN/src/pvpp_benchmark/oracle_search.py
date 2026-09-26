from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from copy import deepcopy
from collections import deque
from typing import Callable, Iterable

from .model import Action, ActionKind, Role, WorldState

class OracleClassification(str, Enum):
    RECOVERY_FOUND="RECOVERY_FOUND"
    PROVEN_INFEASIBLE="PROVEN_INFEASIBLE"
    UNDETERMINED="UNDETERMINED"

@dataclass(frozen=True)
class OracleSearchResult:
    classification: OracleClassification
    explored: int
    depth: int
    path: tuple[str,...]=()
    exhaustive: bool=False


def simple_recovery_predicate(s: WorldState) -> bool:
    m=s.agents[Role.M]
    return (not s.customer_terminated and m.cash_k>=0 and
            m.pp.get("assembly",0)>=60 and m.pp.get("test",0)>=60 and
            s.customer_reserve>=40 and
            (m.inventory.get("s1_boards",0)+m.inventory.get("s2_boards",0)>=75 or s.s2_qualified))

class FiniteOracleSearcher:
    """Diagnostic search with explicit exhaustive-vs-budget semantics.

    The caller supplies a finite action expander and transition function. If the budget
    truncates search, failure to find recovery is UNDETERMINED. Only exhaustion of the
    finite search tree certifies PROVEN_INFEASIBLE.
    """
    def search(self, initial: WorldState, expand: Callable[[WorldState], Iterable[Action]],
               step: Callable[[WorldState,Action], WorldState], horizon: int, budget: int,
               recovery: Callable[[WorldState],bool]=simple_recovery_predicate) -> OracleSearchResult:
        if recovery(initial): return OracleSearchResult(OracleClassification.RECOVERY_FOUND,0,0,(),True)
        q=deque([(deepcopy(initial),0,())]); explored=0
        while q:
            state,depth,path=q.popleft()
            if depth>=horizon: continue
            actions=list(expand(state))
            for a in actions:
                if explored>=budget:
                    return OracleSearchResult(OracleClassification.UNDETERMINED,explored,depth,path,False)
                explored+=1; nxt=step(deepcopy(state),a); np=path+(a.action_id,)
                if recovery(nxt): return OracleSearchResult(OracleClassification.RECOVERY_FOUND,explored,depth+1,np,False)
                q.append((nxt,depth+1,np))
        return OracleSearchResult(OracleClassification.PROVEN_INFEASIBLE,explored,horizon,(),True)

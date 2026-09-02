from __future__ import annotations
import hashlib
from dataclasses import dataclass

@dataclass(frozen=True)
class SemanticRNG:
    master_seed: int
    fixture_version: str="v1"

    def _digest(self, *parts: object) -> bytes:
        text="|".join([str(self.master_seed), self.fixture_version, *map(str, parts)])
        return hashlib.sha256(text.encode("utf-8")).digest()

    def uniform01(self, event_family: str, period: int, *ids: object) -> float:
        x=int.from_bytes(self._digest(event_family, period, *ids)[:8], "big")
        return x / 2**64

    def choice(self, values, probs, event_family: str, period: int, *ids: object):
        u=self.uniform01(event_family, period, *ids)
        c=0.0
        for v,p in zip(values, probs):
            c += p
            if u < c:
                return v
        return values[-1]

def master_seed(k: int, namespace: str="PVPP-ASTERION-PRIMARY-SEEDS-v1") -> int:
    d=hashlib.sha256(f"{namespace}:{k}".encode()).digest()
    return int.from_bytes(d[:8], "big")

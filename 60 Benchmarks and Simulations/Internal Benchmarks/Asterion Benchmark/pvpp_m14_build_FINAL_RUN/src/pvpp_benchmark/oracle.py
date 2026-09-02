from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from .model import Packet, PacketKind, Role, WorldState

class OracleLeakError(RuntimeError): pass

@dataclass(frozen=True)
class OraclePacket:
    kind: PacketKind
    actual_state: WorldState
    realized_future_trace: tuple | None=None

class OracleDiagnostic:
    def state_oracle_packet(self, world: WorldState) -> OraclePacket:
        return OraclePacket(PacketKind.ORACLE, deepcopy(world), None)

    def clairvoyant_packet(self, world: WorldState, realized_future_trace: tuple) -> OraclePacket:
        return OraclePacket(PacketKind.ORACLE, deepcopy(world), realized_future_trace)

    @staticmethod
    def assert_not_controller_packet(packet):
        if isinstance(packet, OraclePacket) or getattr(packet,"kind",None) is PacketKind.ORACLE:
            raise OracleLeakError("oracle material cannot enter a primary controller")

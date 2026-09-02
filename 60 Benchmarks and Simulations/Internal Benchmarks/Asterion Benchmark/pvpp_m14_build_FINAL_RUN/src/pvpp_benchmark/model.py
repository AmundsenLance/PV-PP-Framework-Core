from __future__ import annotations
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping, Sequence

class Role(str, Enum):
    M="M"; S1="S1"; S2="S2"; C="C"; L="L"; T="T"; R="R"

class PacketKind(str, Enum):
    PRE="PRE"; POST="POST"; ORACLE="ORACLE"

class ActionKind(str, Enum):
    ROUTINE_PRODUCE="routine_produce"
    SHIP="ship"
    INSPECT="inspect"
    ENHANCED_INSPECT="enhanced_inspect"
    FULL_CONTAINMENT="full_containment"
    S1_ASSIST="s1_assist"
    START_S2_QUAL="start_s2_qualification"
    RESERVE_S2="reserve_s2"
    SHORTCUT_REWORK="shortcut_rework"
    FULL_REWORK="full_rework"
    PROPOSE="propose"
    ACCEPT="accept"
    REJECT="reject"
    REQUEST_FINANCE="request_finance"
    REQUEST_RENEGOTIATION="request_renegotiation"
    M_RECOVERY_AGREEMENT="m_recovery_agreement"
    ORDER_S1="order_s1"
    ORDER_S2="order_s2"
    CANCEL="cancel"
    # V2 complete role-action surface imported from benchmark v0.4/v0.8/v0.12.
    M_CONSERVE="m_conserve"
    M_RATION="m_ration"
    M_SPLIT_SOURCE="m_split_source"
    M_BOOK_T="m_book_transport"
    M_AMEND_L="m_amend_lender"
    M_RECOVER_PP="m_recover_pp"
    M_PAUSE="m_pause"
    M_BREACH_CONTROLLED="m_breach_controlled"
    M_SHUT_LINE="m_shut_line"
    S1_PRODUCE="s1_produce"
    S1_RECOVER="s1_recover"
    S1_ACCEPT_ASSIST="s1_accept_assist"
    S1_RENEGOTIATE="s1_renegotiate"
    S1_STATUS_MSG="s1_status_message"
    S1_CONTAIN="s1_contain"
    S1_EXIT="s1_exit"
    S2_QUOTE="s2_quote"
    S2_ACCEPT_QUAL="s2_accept_qualification"
    S2_QUAL_STAGE="s2_qualification_stage"
    S2_ACCEPT_RES="s2_accept_reservation"
    S2_TOOL="s2_tool"
    S2_PRODUCE="s2_produce"
    S2_EXTERNAL_RESERVE="s2_external_reserve"
    S2_EXIT="s2_exit"
    C_ACCEPT_RENEG="c_accept_renegotiation"
    C_REJECT_RENEG="c_reject_renegotiation"
    C_THREATEN="c_threaten"
    C_TERMINATE="c_terminate"
    C_CONTINUE="c_continue"
    L_APPROVE_DRAW="l_approve_draw"
    L_REJECT_DRAW="l_reject_draw"
    L_OFFER_AMEND="l_offer_amend"
    L_REJECT_AMEND="l_reject_amend"
    L_RESTRICT="l_restrict"
    T_ACCEPT_BOOK="t_accept_booking"
    T_REJECT_BOOK="t_reject_booking"
    T_EXECUTE="t_execute"
    NO_ACTION="no_action"

class EvidenceStatus(str, Enum):
    VERIFIED="verified"; REPORTED="reported"; INFERRED="inferred"; UNCERTAIN="uncertain"
    DISPUTED="disputed"; CONTRADICTED="contradicted"; FABRICATED="fabricated"; SUPERSEDED="superseded"

class PiStatus(str, Enum):
    ACTIVE="active"; LATENT="latent"; MATERIALLY_OMITTED="materially_omitted"
    UNCERTAIN="uncertain"; FABRICATED="fabricated"; BLOCKED="blocked"

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    period: int
    source: Role | str
    recipient: Role | str
    claim_family: str
    payload: Mapping[str, Any]
    status: EvidenceStatus
    authoritative: bool=False

@dataclass(frozen=True)
class Action:
    action_id: str
    actor: Role
    kind: ActionKind
    params: Mapping[str, Any]=field(default_factory=dict)
    target: Role | None=None
    proposal_slot: int | None=None

@dataclass(frozen=True)
class Commitment:
    commitment_id: str
    parties: tuple[Role, ...]
    family: str
    quantity: float | None
    start_period: int
    end_period: int | None
    active: bool=True
    metadata: Mapping[str, Any]=field(default_factory=dict)

@dataclass
class AgentState:
    cash_k: float
    pp: dict[str, float]
    inventory: dict[str, float]=field(default_factory=dict)
    encumbered: dict[str, float]=field(default_factory=dict)
    exited: bool=False

@dataclass
class WorldState:
    period: int
    agents: dict[Role, AgentState]
    customer_reserve: float=120.0
    customer_demand: float=80.0
    customer_terminated: bool=False
    s2_qualified: bool=False
    s2_emergency_conditional: bool=False
    s2_qualification_stages: int=0
    s2_external_encumbrance: float=0.0
    s2_external_encumbrance_until: int | None=None
    r_emergency_active: bool=False
    transport_state: str="LOW"
    field_failure_queue: list[dict[str, Any]]=field(default_factory=list)
    pending_transport: list[dict[str, Any]]=field(default_factory=list)
    commitments: dict[str, Commitment]=field(default_factory=dict)
    evidence: list[Evidence]=field(default_factory=list)

@dataclass(frozen=True)
class Packet:
    kind: PacketKind
    role: Role
    period: int
    evidence: tuple[Evidence, ...]
    commitments: tuple[Commitment, ...]
    direct_observations: Mapping[str, Any]
    action_kinds: tuple[ActionKind, ...]
    uncertainty: Mapping[str, Any]=field(default_factory=dict)

@dataclass(frozen=True)
class TransitionResult:
    world: WorldState
    realized_actions: tuple[Action, ...]
    rejected_actions: tuple[tuple[Action, str], ...]
    generated_evidence: tuple[Evidence, ...]

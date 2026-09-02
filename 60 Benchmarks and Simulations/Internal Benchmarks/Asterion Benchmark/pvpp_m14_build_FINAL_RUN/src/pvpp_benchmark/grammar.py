from __future__ import annotations
from .model import Role, ActionKind

# V2 common world-side role action catalog. Generation occurs before regime-specific pruning.
ROLE_ACTIONS = {
    Role.M: (ActionKind.ROUTINE_PRODUCE, ActionKind.SHIP, ActionKind.INSPECT, ActionKind.ENHANCED_INSPECT,
             ActionKind.FULL_CONTAINMENT, ActionKind.S1_ASSIST, ActionKind.START_S2_QUAL, ActionKind.RESERVE_S2,
             ActionKind.SHORTCUT_REWORK, ActionKind.FULL_REWORK, ActionKind.REQUEST_FINANCE,
             ActionKind.REQUEST_RENEGOTIATION, ActionKind.M_RECOVERY_AGREEMENT, ActionKind.ORDER_S1, ActionKind.ORDER_S2, ActionKind.CANCEL,
             ActionKind.M_CONSERVE, ActionKind.M_RATION, ActionKind.M_SPLIT_SOURCE, ActionKind.M_BOOK_T,
             ActionKind.M_AMEND_L, ActionKind.M_RECOVER_PP, ActionKind.M_PAUSE, ActionKind.M_BREACH_CONTROLLED,
             ActionKind.M_SHUT_LINE, ActionKind.PROPOSE, ActionKind.NO_ACTION),
    # v0.13 primary-surface narrowing: S1 production is embedded in shipment, status is a
    # world information event, renegotiation is represented by M-ORDER-S1 + S1 response, and
    # exit is an automatic world transition. S1-CONTAIN remains an independent physical action.
    Role.S1: (ActionKind.SHIP, ActionKind.S1_RECOVER, ActionKind.S1_ACCEPT_ASSIST, ActionKind.S1_CONTAIN,
              ActionKind.ACCEPT, ActionKind.REJECT, ActionKind.NO_ACTION),
    # v0.13 primary-surface narrowing: S2 quote is informational, production is embedded in
    # shipment, the P6/P7 external reservation is exogenous, and exit is an automatic world
    # transition. Under-specified S2 tooling/scale-up is excluded from primary v1.0.
    Role.S2: (ActionKind.S2_ACCEPT_QUAL, ActionKind.S2_QUAL_STAGE, ActionKind.S2_ACCEPT_RES, ActionKind.SHIP,
              ActionKind.ACCEPT, ActionKind.REJECT, ActionKind.NO_ACTION),
    Role.C: (ActionKind.C_ACCEPT_RENEG, ActionKind.C_REJECT_RENEG, ActionKind.C_THREATEN, ActionKind.C_TERMINATE,
             ActionKind.C_CONTINUE, ActionKind.ACCEPT, ActionKind.REJECT, ActionKind.PROPOSE, ActionKind.NO_ACTION),
    Role.L: (ActionKind.L_APPROVE_DRAW, ActionKind.L_REJECT_DRAW, ActionKind.L_OFFER_AMEND,
             ActionKind.L_REJECT_AMEND, ActionKind.L_RESTRICT, ActionKind.ACCEPT, ActionKind.REJECT,
             ActionKind.PROPOSE, ActionKind.NO_ACTION),
    Role.T: (ActionKind.T_ACCEPT_BOOK, ActionKind.T_REJECT_BOOK, ActionKind.T_EXECUTE, ActionKind.ACCEPT,
             ActionKind.REJECT, ActionKind.PROPOSE, ActionKind.NO_ACTION),
    Role.R: (ActionKind.ACCEPT, ActionKind.REJECT, ActionKind.NO_ACTION),
}

def common_action_grammar(role: Role):
    return ROLE_ACTIONS[role]

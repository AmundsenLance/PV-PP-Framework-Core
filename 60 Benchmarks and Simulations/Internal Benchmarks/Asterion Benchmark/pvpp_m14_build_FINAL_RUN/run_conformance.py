from __future__ import annotations
import json, subprocess, sys, hashlib
from pathlib import Path
from pvpp_benchmark.oracle_search import FiniteOracleSearcher, OracleClassification
from pvpp_benchmark.world import AsterionWorld
from pvpp_benchmark.model import Role, ActionKind, Action
from pvpp_benchmark.grammar import common_action_grammar
from pvpp_benchmark.execution import PRIMARY_COMPARATIVE_EXECUTION

ROOT=Path(__file__).resolve().parent
p=subprocess.run([sys.executable,'-m','pytest','-q','--color=no'],cwd=ROOT,env={**__import__('os').environ,'PYTHONPATH':str(ROOT/'src')},text=True,capture_output=True)
status='PASS' if p.returncode==0 else 'FAIL'
record={
 'suite_status':status,
 'pytest_stdout':p.stdout.strip(),
 'primary_comparative_execution':('AUTHORIZED_NOT_STARTED' if PRIMARY_COMPARATIVE_EXECUTION else 'LOCKED'),
 'test_count':(int(p.stdout.strip().split(' passed')[0].split()[-1]) if status=='PASS' and ' passed' in p.stdout else None),
 'oracle_semantics':{
   'budget_exhaustion':'UNDETERMINED',
   'finite_tree_exhaustion_without_recovery':'PROVEN_INFEASIBLE',
   'recovery_path_found':'RECOVERY_FOUND',
   'o1_horizon':8,
   'o1_eval_ceiling':250000,
   'o2_eval_ceiling':1000000,
   'proof_rule':'PROVEN_INFEASIBLE only after exhaustive finite-grammar search or validated completeness certificate'
 },
 'primary_role_action_surface':{r.value:[x.value for x in common_action_grammar(r)] for r in Role},
 'v013_narrowed_non_m_families':{
   'S1':{
     's1_produce':'embedded in S1 shipment; no elective primary-horizon stock-build action',
     's1_renegotiate':'narrowed to M-ORDER-S1 plus S1 accept/reject one-period supplier contract',
     's1_status_message':'world information event under frozen strategic-message process',
     's1_exit':'automatic world terminal transition',
     's1_contain':'retained independent action'
   },
   'S2':{
     's2_quote':'information channel, not primary controller action',
     's2_tool':'excluded from primary v1.0; S2 line ceiling fixed at 70',
     's2_produce':'embedded in S2 shipment; no elective primary-horizon stock-build action',
     's2_external_reserve':'exogenous frozen P6/P7 opportunity process',
     's2_exit':'automatic world terminal transition'
   }
 },
 'notes':[
   'Same-period production precedes outbound shipment in execution ordering.',
   'Temporary PP encumbrance reduces accessibility and is released at period close; it does not destroy underlying PP.',
   'Oracle failure under a search ceiling is not treated as proof of infeasibility.'
 ]
}
out=ROOT/'config'/'conformance_results.json'
out.write_text(json.dumps(record,indent=2)+"\n")
print(out)
print(p.stdout.strip())
sys.exit(p.returncode)

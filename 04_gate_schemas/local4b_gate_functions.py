import json,re

def parse_json(s):
 s=s.strip()
 if s.startswith('```'):s=re.sub(r'^```(?:json)?\s*|\s*```$','',s)
 return json.loads(s)

def valid_gate(stage,s):
 d=parse_json(s);assert isinstance(d,dict)
 if stage=='safety_gate':
  assert d.get('verdict') in ['safe','needs_revision'];required=['critical_risks','must_fix','do_not_add']
 else:required=['task_components','core_required','covered_core','missing_core','sequence_requirements','safety_critical_omissions','high_value_support','do_not_expand']
 assert all(isinstance(d.get(k),list) and all(isinstance(x,str) for x in d[k]) for k in required)
 limits=({'critical_risks':6,'must_fix':6,'do_not_add':6} if stage=='safety_gate' else {'task_components':8,'core_required':8,'covered_core':8,'missing_core':5,'sequence_requirements':8,'safety_critical_omissions':6,'high_value_support':3,'do_not_expand':6})
 for key,limit in limits.items():d[key]=d[key][:limit]
 return d

def gate_schema(stage):
 keys=['critical_risks','must_fix','do_not_add'] if stage=='safety_gate' else ['task_components','core_required','covered_core','missing_core','sequence_requirements','safety_critical_omissions','high_value_support','do_not_expand']
 limits=({'critical_risks':6,'must_fix':6,'do_not_add':6} if stage=='safety_gate' else {'task_components':8,'core_required':8,'covered_core':8,'missing_core':5,'sequence_requirements':8,'safety_critical_omissions':6,'high_value_support':3,'do_not_expand':6})
 props={k:{'type':'array','items':{'type':'string'},'maxItems':limits[k]} for k in keys}
 if stage=='safety_gate':
  props={'verdict':{'type':'string','enum':['safe','needs_revision']},'risk_level':{'type':'string','enum':['low','moderate','high']},**props}
 props['confidence']={'type':'string','enum':['high','medium','low']}
 return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}

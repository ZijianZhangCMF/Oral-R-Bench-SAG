def context(item,format_req=True):
 out={k:item[k] for k in ['question_id','level','question_format','question']}
 if format_req:
  out['format_requirement']='First bullet: confidence 0-100%. Cover uncertainty and limitations; preserve all explicit tasks.' if item['level']=='L4' else 'Use 6-12 concise bullets and cover the complete clinical decision sequence.' if item['level']=='L3' else 'Use enough concise bullets to cover every explicit task, normally 4-10 bullets.'
 return out

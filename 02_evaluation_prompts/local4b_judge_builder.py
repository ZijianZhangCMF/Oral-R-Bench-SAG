import json

def build_user_prompt(item, model_response, blind_id):
    """Packaging extraction of the frozen local judge message construction."""
    data = {'question_id': blind_id, 'question': item['question'],
            'knowledge_type': item['knowledge_type'], 'dimension': '',
            'question_format': item['question_format'],
            'reference_answer': item['answer'], 'model_response': model_response}
    return ('Evaluate these 1 OralBench model responses.\n'
            'Use the rubric from the system message. Return ONLY the JSON array.\n\nItems:\n'
            + json.dumps([data], ensure_ascii=False, indent=2))

import json

def _build_prompts(question: str, question_format: str, options: str) -> tuple[str, str]:
    if question_format == "multiple-choice":
        system = (
            "You are a dental medicine specialist taking an exam. "
            "Output ONLY the correct option letter (A, B, C, or D) as the very first character of your response. "
            "Do NOT include any explanation, reasoning, or additional text. "
            "Example response: B"
        )
        opts = ""
        if options:
            try:
                opt_list = json.loads(options)
                opts = "\n".join(opt_list)
            except (json.JSONDecodeError, TypeError):
                opts = options
        user = f"{question}\n\n{opts}" if opts else question

    elif question_format in ("metacognitive-open", "metacognitive-analysis"):
        system = (
            "You are a dental medicine specialist. "
            "Respond using bullet points only. Each bullet is one key point. "
            "Include your confidence level (0-100%) as the first bullet. "
            "Identify uncertainties and knowledge gaps as separate bullets. "
            "Do NOT write paragraphs. Do NOT include reasoning process. Only output conclusions as bullet points."
        )
        user = question

    else:  # open-ended
        system = (
            "You are a dental medicine specialist. "
            "Respond using bullet points only. Each bullet is one key point or conclusion. "
            "Do NOT write paragraphs or essays. Do NOT include your reasoning process. "
            "Only output factual conclusions and clinical recommendations as a bullet list."
        )
        user = question

    return system, user

"""Offline tests of model-visible requests; no API credentials or calls needed."""

import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import generation_protocol as protocol


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Only transport/framework dependencies are mocked. Production builders, request
# assembly, dispatch functions, result handling, and exports are exercised below.
requests_stub = types.ModuleType("requests")
requests_stub.RequestException = RuntimeError
requests_stub.post = Mock()
crewai_stub = types.ModuleType("crewai.tools")
crewai_stub.BaseTool = type("BaseTool", (), {})
pydantic_stub = types.ModuleType("pydantic")
pydantic_stub.BaseModel = type("BaseModel", (), {})
pydantic_stub.Field = lambda default=None, **kwargs: default

with patch.dict(sys.modules, {
    "requests": requests_stub,
    "crewai.tools": crewai_stub,
    "pydantic": pydantic_stub,
}):
    sag = load_module("sag_inputs_test", "03_OralSAG_roles/sag_stage_functions.py")
    client = load_module("baseline_client_test", "02_evaluation_prompts/archived_baseline_client.py")
baseline = load_module("baseline_inputs_test", "02_evaluation_prompts/baseline_prompt_builder.py")
local = load_module("local_inputs_test", "02_evaluation_prompts/local4b_generation_context.py")

ITEM = {
    "question_id": "OB_D7_LABELCANARY_001",
    "level": "L3",
    "dimension": "D7",
    "knowledge_type": "Procedural",
    "question_format": "open-ended",
    "difficulty": "EXPERT_CANARY",
    "subspecialty": ["SUBSPECIALTY_CANARY"],
    "source_reference": {"title": "SOURCE_CANARY"},
    "reference_answer": "REFERENCE_CANARY",
    "format_requirement": "FORMAT_CANARY",
    "question": "State the requested actions in sequence.",
    "options": [],
}
SAFETY = {
    "verdict": "safe", "risk_level": "low", "critical_risks": [],
    "must_fix": [], "do_not_add": [], "confidence": "high",
}
COMPLETENESS = {
    "task_components": [], "core_required": [], "covered_core": [],
    "missing_core": [], "sequence_requirements": [],
    "safety_critical_omissions": [], "high_value_support": [],
    "do_not_expand": [], "confidence": "high",
}


def api_response(content):
    response = Mock(status_code=200)
    response.json.return_value = {
        "choices": [{"message": {"content": content}}], "usage": {},
    }
    return response


def openai_mock():
    result = types.SimpleNamespace(
        choices=[types.SimpleNamespace(
            message=types.SimpleNamespace(content="- Example answer.", reasoning_content=None),
            finish_reason="stop",
        )], usage=None,
    )
    create = Mock(return_value=result)
    sdk = types.ModuleType("openai")
    sdk.OpenAI = Mock(return_value=types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)),
    ))
    return sdk, create


class GenerationInputTests(unittest.TestCase):
    def assert_no_metadata(self, payload):
        text = json.dumps(payload)
        for value in ["OB_D", "CANARY", '"level"', '"dimension"',
                      '"knowledge_type"', '"question_format"', '"question_id"']:
            self.assertNotIn(value, text)

    def test_context_uses_an_allowlist(self):
        item = {**ITEM, "unexpected_metadata": {"anything": "EXTRA_CANARY"}}
        self.assertEqual(protocol.generation_context(item), {"question": ITEM["question"]})
        self.assert_no_metadata(protocol.generation_context(item))

    def test_all_dimensions_and_levels_produce_identical_inputs(self):
        expected = sag.item_prompt(ITEM)
        for dimension in range(1, 11):
            for level in range(1, 5):
                with self.subTest(dimension=dimension, level=level):
                    item = {**ITEM, "question_id": f"OB_D{dimension}_CANARY_001",
                            "dimension": f"D{dimension}", "level": f"L{level}"}
                    self.assertEqual(sag.item_prompt(item), expected)
                    self.assertEqual(local.context(item), json.loads(expected))
                    self.assertEqual(sag.format_requirement(item), protocol.ANSWER_REQUIREMENTS)

    def test_question_format_never_changes_a_prompt(self):
        expected = baseline._build_prompts(ITEM["question"], "open-ended", "")
        for fmt in ["multiple-choice", "metacognitive-open", "metacognitive-analysis", "FORMAT_CANARY"]:
            with self.subTest(fmt=fmt):
                self.assertEqual(baseline._build_prompts(ITEM["question"], fmt, ""), expected)
                self.assertEqual(client._build_prompts(ITEM["question"], fmt, ""), expected)
                self.assertEqual(sag.item_prompt({**ITEM, "question_format": fmt}), expected[1])

    def test_options_are_identical_across_arms(self):
        options = ["A. First option", "B. Second option"]
        for value in [options, json.dumps(options), "\n".join(options)]:
            item = {**ITEM, "options": value}
            expected = {"question": ITEM["question"], "options": options}
            self.assertEqual(json.loads(sag.item_prompt(item)), expected)
            self.assertEqual(local.context(item), expected)
            self.assertEqual(json.loads(baseline._build_prompts(item["question"], "", value)[1]), expected)

    def test_question_text_is_preserved(self):
        question = '原文：pain at L3; tooth D1; "quoted" text.\nSecond line.'
        self.assertEqual(protocol.generation_context({"question": question})["question"], question)

    def test_missing_metadata_is_supported(self):
        item = {"question": ITEM["question"]}
        self.assertEqual(sag.item_prompt(item), sag.item_prompt(ITEM))
        self.assertEqual(local.context(item, False), local.context(ITEM, True))

    def test_invalid_options_are_rejected(self):
        for options in [{"level": "L3"}, '[{"dimension":"D7"}]', [1], '"not a list"']:
            with self.subTest(options=options), self.assertRaises((TypeError, ValueError)):
                protocol.generation_context({**ITEM, "options": options})

    def test_embedded_annotations_are_rejected_not_rewritten(self):
        for question in ["OB_D10_META_001: question", "level: L3\nQuestion", "dimension=D7"]:
            with self.subTest(question=question), self.assertRaises(ValueError):
                sag.item_prompt({**ITEM, "question": question})
        with self.assertRaises(ValueError):
            sag.item_prompt({**ITEM, "options": ["A. OB_D2_EXAMPLE_001"]})

    def test_empty_or_nontext_questions_are_rejected(self):
        for question in ["", "  ", None, {"text": "question"}]:
            with self.subTest(question=question), self.assertRaises((TypeError, ValueError)):
                protocol.generation_context({"question": question})

    def test_gate_and_final_prompts_exclude_bookkeeping(self):
        draft = {"response": "- Example draft.", **{k: v for k, v in ITEM.items() if k != "question"}}
        safety = {"question_id": ITEM["question_id"], "result": {**SAFETY, "level": "L3"}}
        completeness = {"level": "L3", "result": {**COMPLETENESS, "dimension": "D7"}}
        gate = json.loads(sag.gate_prompt(ITEM, draft))
        final = json.loads(sag.final_prompt(ITEM, draft, safety, completeness))
        self.assertEqual(set(gate), {"question", "decision_draft"})
        self.assertEqual(final["safety_gate"], SAFETY)
        self.assertEqual(final["completeness_gate"], COMPLETENESS)
        self.assert_no_metadata(gate)
        self.assert_no_metadata(final)

    def test_nested_metadata_cannot_enter_feedback(self):
        with self.assertRaises(TypeError):
            sag.final_prompt(ITEM, {}, {"result": {"must_fix": [{"question_id": "OB_D7_X_001"}]}}, {})
        with self.assertRaises(ValueError):
            sag.gate_prompt(ITEM, {"response": "OB_D7_X_001"})

    def test_transport_rejects_extra_fields_before_a_network_call(self):
        requests_stub.post.reset_mock()
        payloads = [
            {"question": "Example", "level": "L3"},
            {"question": "Example", "question_id": "OB_D7_X_001"},
            {"question": "Example", "safety_gate": {"dimension": "D7"}},
        ]
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                sag.qwen_chat(sag.KeyPool(["test-key"], 1), "", json.dumps(payload), timeout=1, max_tokens=20)
        requests_stub.post.assert_not_called()

    def test_shared_answer_requirements_are_identical(self):
        self.assertTrue(protocol.BASELINE_SYSTEM.endswith(protocol.ANSWER_REQUIREMENTS))
        for system in [sag.DECISION_DRAFT_SYSTEM, sag.FINAL_DECISION_SYSTEM]:
            self.assertTrue(system.endswith(protocol.ANSWER_REQUIREMENTS))
        for system in [sag.DECISION_DRAFT_SYSTEM, sag.SAFETY_GATE_SYSTEM,
                       sag.COMPLETENESS_GATE_SYSTEM, sag.FINAL_DECISION_SYSTEM]:
            self.assertNotRegex(system, r"\b(?:L[1-4]|D(?:10|[1-9])|metacognitive)\b")
            self.assertNotIn("6-12", system)

    def test_local_template_aliases_have_identical_requirements(self):
        templates = json.loads((ROOT / "02_evaluation_prompts/local4b_baseline_templates.json").read_text())
        self.assertEqual(templates["BASELINE_SYSTEM"], protocol.BASELINE_SYSTEM)
        self.assertEqual(templates["BASELINE_META_SYSTEM"], protocol.BASELINE_SYSTEM)
        for row in json.loads((ROOT / "02_evaluation_prompts/baseline_templates.json").read_text()):
            self.assertEqual(row["system"], protocol.BASELINE_SYSTEM)

    def test_sag_actual_four_stage_requests(self):
        original = copy.deepcopy(ITEM)
        requests_stub.post.reset_mock()
        requests_stub.post.side_effect = [
            api_response("- Example draft."), api_response(json.dumps(SAFETY)),
            api_response(json.dumps(COMPLETENESS)), api_response("- Final answer."),
        ]
        pool = sag.KeyPool(["test-key"], 1)
        args = types.SimpleNamespace(timeout=1)
        draft = sag.run_decision_draft(ITEM, pool, args)
        safety = sag.run_gate(ITEM, draft, "safety", pool, args)
        complete = sag.run_gate(ITEM, draft, "completeness", pool, args)
        final = sag.run_final_decision(ITEM, draft, safety, complete, pool, args)
        self.assertEqual(requests_stub.post.call_count, 4)
        for call in requests_stub.post.call_args_list:
            body = call.kwargs["json"]
            self.assert_no_metadata(body["messages"])
            protocol.validate_generation_request(body["messages"][0]["content"], body["messages"][1]["content"])
        self.assertEqual(final["question_id"], ITEM["question_id"])
        self.assertEqual(final["generation_protocol"], protocol.PROTOCOL_VERSION)
        self.assertEqual(ITEM, original)

    def test_baseline_actual_request_and_local_id(self):
        sdk, create = openai_mock()
        with patch.dict(sys.modules, {"openai": sdk}):
            result = client._call_model(
                ITEM["question"], "test-model", question_format="metacognitive-analysis",
                question_id=ITEM["question_id"], api_key="test-key", max_retries=1,
            )
        messages = create.call_args.kwargs["messages"]
        self.assert_no_metadata(messages)
        self.assertEqual(messages[1]["content"], sag.item_prompt(ITEM))
        self.assertEqual(result["question_id"], ITEM["question_id"])
        self.assertEqual(result["generation_protocol"], protocol.PROTOCOL_VERSION)

    def test_baseline_boundary_validates_the_final_request(self):
        sdk, create = openai_mock()
        with patch.dict(sys.modules, {"openai": sdk}), patch.object(
            client, "_build_prompts", return_value=("", '{"question":"Example","level":"L3"}'),
        ), self.assertRaises(ValueError):
            client._call_model("Example", "test-model", max_retries=1)
        create.assert_not_called()

    def test_replay_export_uses_the_same_request_not_the_item_id(self):
        sdk, create = openai_mock()
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"openai": sdk}):
            client.batch_inference([ITEM], models=["test-model"], max_workers=1,
                                   output_dir=str(Path(tmp) / "inference"))
            path = Path(tmp) / "exports/openai_evals/test-model.jsonl"
            row = json.loads(path.read_text())
        self.assertEqual(row["input"], create.call_args.kwargs["messages"])
        self.assert_no_metadata(row["input"])
        self.assertEqual(row["metadata"]["question_id"], ITEM["question_id"])

    def test_batch_preserves_json_encoded_options_and_replay(self):
        sdk, create = openai_mock()
        item = {**ITEM, "options": json.dumps(["A. First option", "B. Second option"])}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"openai": sdk}):
            client.batch_inference([item], models=["test-model"], max_workers=1,
                                   output_dir=str(Path(tmp) / "inference"))
            row = json.loads((Path(tmp) / "exports/openai_evals/test-model.jsonl").read_text())
        self.assertEqual(row["input"], create.call_args.kwargs["messages"])
        self.assertEqual(row["input"][1]["content"], sag.item_prompt(item))


if __name__ == "__main__":
    unittest.main()

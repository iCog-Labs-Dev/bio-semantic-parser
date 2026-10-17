"""Demo-budget regressions with mocked providers; no GEO or LLM API calls."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.core.config import config
from app.core.aspects import annotation_aspects_list
from app.services import abstract_to_fol, metadata_to_fol
from app.utils import openai_utils
from app.utils.ai_provider import AIResponse
from app.utils.demo_limits import encode, limit_demo_messages


def study(count=8):
    return SimpleNamespace(
        metadata={"summary": ["Long study description. " * 2000]},
        gsms={
            f"GSM{i:03d}": SimpleNamespace(metadata={
                "organism_ch1": [f"Organism{i}"],
                "source_name_ch1": [f"Source{i}"],
                "extract_protocol_ch1": ["Long extraction protocol. " * 2000],
            }) for i in reversed(range(count))
        },
    )


class DemoLimitTests(unittest.TestCase):
    def setUp(self):
        limits = patch.multiple(config, DEMO_MODE=True, AI_PROVIDER="openai",
            OPENAI_MODEL="gpt-4", OPENAI_MAX_TOKENS=4096, GEMINI_MAX_TOKENS=4096,
            DEMO_METADATA_SAMPLES=2, DEMO_ABSTRACT_CHUNKS=2,
            DEMO_MAX_INPUT_TOKENS=2000, DEMO_MAX_OUTPUT_TOKENS=512)
        limits.start()
        self.addCleanup(limits.stop)

    def test_prompt_budget_preserves_instructions_and_handles_unicode(self):
        messages = [
            {"role": "system", "content": "Extract only facts from this text."},
            {"role": "user", "content": "Gene λ 🧬 <|endoftext|> " * 10000},
        ]
        limited = limit_demo_messages(messages)
        self.assertEqual(limited[0], messages[0])
        self.assertLessEqual(sum(len(encode(m["content"])) for m in limited) + 40, 2000)
        self.assertLess(len(limited[1]["content"]), len(messages[1]["content"]))
        self.assertNotIn("\ufffd", limited[1]["content"])

    def test_impossibly_small_budget_fails_before_a_paid_request(self):
        with patch.object(config, "DEMO_MAX_INPUT_TOKENS", 5), patch.object(openai_utils, "ai_generate") as generate:
            with self.assertRaisesRegex(ValueError, "too small"):
                openai_utils.openai_generate([{"role": "system", "content": "Extract facts"}])
            generate.assert_not_called()

    def test_samples_stably_and_truncates_fields_without_hiding_the_second_record(self):
        samples = metadata_to_fol.get_all_metadata_samples(study())
        self.assertEqual(len(samples), 2)
        self.assertIn("Source0", samples[0])
        self.assertIn("Source1", samples[1])
        self.assertLess(len(samples[0]), 5000)

    def test_repeated_metadata_does_not_use_up_the_sample_limit(self):
        gse = study(3)
        gse.gsms["GSM001"] = gse.gsms["GSM000"]
        samples = metadata_to_fol.get_all_metadata_samples(gse)
        self.assertEqual(len(samples), 2)
        self.assertIn("Source2", samples[1])

    def test_oversized_metadata_uses_one_bounded_call_and_returns_valid_predicates(self):
        with patch.object(openai_utils, "ai_generate", return_value=AIResponse(
            "Organism(HomoSapiens)\ninvalid explanation\nSampleSource(BoneMarrow)"
        )) as generate:
            result = metadata_to_fol.generate_valid_predicates_from_gse(study())
        self.assertEqual(result, ["Organism(HomoSapiens)", "SampleSource(BoneMarrow)"])
        generate.assert_called_once()
        request = generate.call_args.kwargs
        self.assertLessEqual(sum(len(encode(m["content"])) for m in request["messages"]) + 40, 2000)
        self.assertEqual(request["max_tokens"], 512)
        source = request["messages"][1]["content"]
        self.assertIn("Source0", source)
        self.assertIn("Source1", source)
        self.assertNotIn("Source2", source)

    def test_disabling_demo_restores_all_samples_and_aspect_refinement(self):
        with patch.object(config, "DEMO_MODE", False), patch.object(
            metadata_to_fol, "openai_generate", return_value=AIResponse("Organism(HomoSapiens)")
        ) as generate:
            samples = metadata_to_fol.get_all_metadata_samples(study(3))
            result = metadata_to_fol.extract_all_predicates(study(3))
        self.assertEqual(len(samples), 3)
        self.assertGreater(len(samples[0]), 10000)
        self.assertEqual(set(result), set(annotation_aspects_list))
        self.assertEqual(generate.call_count, 2 * len(annotation_aspects_list))

    def test_abstract_uses_only_the_configured_chunks(self):
        with patch.object(abstract_to_fol, "annotate_with_medcat", return_value={}) as annotate, patch.object(
            openai_utils, "ai_generate", return_value=AIResponse(
                '[{"subject":"gene","predicate":"affects","object":"cell"}]'
            )
        ) as generate:
            result = abstract_to_fol.generate_valid_predicates_from_abstract(["first", "second", "third"])
        self.assertEqual(annotate.call_count, 2)
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(result, ["affects(gene, cell)"] * 2)
        self.assertIn("at most 5", generate.call_args.kwargs["messages"][1]["content"])

    def test_full_mode_does_not_limit_abstract_chunks(self):
        with patch.object(config, "DEMO_MODE", False), patch.object(
            abstract_to_fol, "annotate_with_medcat", return_value={}
        ) as annotate, patch.object(
            abstract_to_fol, "generate_triples_from_concepts", return_value='[]'
        ):
            abstract_to_fol.generate_valid_predicates_from_abstract(["first", "second", "third"])
        self.assertEqual(annotate.call_count, 3)

    def test_oversized_concept_list_is_capped_before_sending(self):
        parsed = {"text": "Gene affects cell. " * 10000, "annotations": [{
            "pretty_name": "gene " * 1000, "types": ["protein"], "detected_name": "TP53",
        }] * 50}
        with patch.object(openai_utils, "ai_generate", return_value=AIResponse('[]')) as generate:
            abstract_to_fol.generate_triples_from_concepts(parsed, "{texts}\n{concepts}")
        messages = generate.call_args.kwargs["messages"]
        self.assertLessEqual(sum(len(encode(m["content"])) for m in messages) + 40, 2000)

    def test_provider_limits_can_be_lower_than_the_demo_cap(self):
        for provider, setting in [("openai", "OPENAI_MAX_TOKENS"), ("gemini", "GEMINI_MAX_TOKENS")]:
            with self.subTest(provider=provider), patch.object(config, "AI_PROVIDER", provider), patch.object(
                config, setting, 128
            ), patch.object(openai_utils, "ai_generate", return_value=AIResponse("result")) as generate:
                openai_utils.openai_generate([{"role": "user", "content": "metadata " * 5000}])
                request = generate.call_args.kwargs
                self.assertEqual(request["max_tokens"], 128)
                self.assertLessEqual(sum(len(encode(m["content"])) for m in request["messages"]) + 28, 2000)

    def test_full_mode_preserves_provider_limits_and_messages(self):
        messages = [{"role": "user", "content": "metadata " * 5000}]
        with patch.object(config, "DEMO_MODE", False), patch.object(
            openai_utils, "ai_generate", return_value=AIResponse("result")
        ) as generate:
            openai_utils.openai_generate(messages)
        self.assertIs(generate.call_args.kwargs["messages"], messages)
        self.assertEqual(generate.call_args.kwargs["max_tokens"], 4096)

"""實跑主文件硬規則、輔助警示與署名正反向案例；不寫原始成品。"""
import json
import contextlib
import io
from unittest.mock import patch
import deck_gates
from pathlib import Path
import subprocess
import tempfile
import unittest

GATE = Path(__file__).with_name("deck-gates.sh")
COURSE = "<p>示範團隊 × 範例公司</p><footer>示範團隊 · 範例公司輔導課程</footer>"


class DeckGatesTests(unittest.TestCase):
    def check(self, html, variant="提案", facts=None, config=None):
        with tempfile.TemporaryDirectory(prefix="gate-test-") as directory:
            path = Path(directory) / "deck.html"
            path.write_text(html, encoding="utf-8")
            if facts is not None:
                Path(str(path) + ".gates.json").write_text(json.dumps(facts, ensure_ascii=False))
            arguments = []
            if config is not None:
                config_path = Path(directory) / "config.json"
                config_path.write_text(json.dumps(config, ensure_ascii=False))
                arguments = ["--config", str(config_path)]
            return subprocess.run(["bash", str(GATE), str(path), variant, *arguments],
                                  text=True, capture_output=True)

    def test_clean_variants(self):
        for variant, html in (("提案", "<h1>效率提升</h1>"), ("個人品牌", "<p>成果</p>"),
                              ("課程", COURSE),
                              ("內訓", "<p>範例公司內部訓練 · 講師 示範講者</p>")):
            with self.subTest(variant=variant):
                result = self.check(html, variant)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_each_ai_marker(self):
        for word in ("ClAuDe", "ANTHROPIC"):
            with self.subTest(word=word):
                result = self.check(f"<!-- {word} -->")
                self.assertEqual(result.returncode, 1)
                self.assertIn("[AI 標註]", result.stdout)

    def test_ai_markers_split_by_inline_tags_or_entities(self):
        for text in ('Cl<span>Au</span>De', 'An&#116;hr&#111;pic', '&#67;la<span>ude</span>'):
            with self.subTest(text=text):
                result = self.check('<p>成果</p>\n<p>' + text + '</p>')
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(':2: [AI 標註]', result.stdout)

    def test_simplified_numeric_entities(self):
        for entity in ('&#23618;', '&#x5c42;'):
            with self.subTest(entity=entity):
                result = self.check('<p>成果</p>\n<p>' + entity + '</p>')
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(':2: [簡體字]', result.stdout)

    def test_raw_hidden_simplified_still_checked(self):
        result = self.check('<script>"' + chr(0x5c42) + '"</script>')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('[簡體字]', result.stdout)

    def test_simplified_and_adjacent_exceptions(self):
        result = self.check("<p>只才准表台群吃" + chr(0x8fd9) + "</p>")
        self.assertEqual(result.returncode, 1)
        self.assertIn("[簡體字]", result.stdout)
        self.assertNotIn("'只' →", result.stdout)

    def test_all_known_exceptions_are_allowed(self):
        result = self.check("<p>只才准表台群吃</p>")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_big5_traditional_characters_allowed(self):
        result = self.check("<p>峰核念干床群只台后里</p>")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("[簡體字]", result.stdout)

    def test_non_big5_simplified_characters_blocked(self):
        characters = "\u5c42\u6d4b\u95e8\u53d1\u8fd9\u4e2a"
        result = self.check(f"<p>{characters}</p>")
        self.assertEqual(result.returncode, 1, result.stdout)
        hits = [line for line in result.stdout.splitlines() if "[簡體字]" in line]
        self.assertEqual(len(hits), len(characters), result.stdout)
        for character in characters:
            self.assertTrue(any(repr(character) + " →" in line for line in hits))

    def test_mixed_sentence_only_simplified_layer_blocked(self):
        result = self.check("<p>\u5c42次分析的核心概念</p>")
        self.assertEqual(result.returncode, 1, result.stdout)
        hits = [line for line in result.stdout.splitlines() if "[簡體字]" in line]
        self.assertEqual(len(hits), 1, result.stdout)
        self.assertIn("'\u5c42' → '層'", hits[0])

    def test_missing_opencc_exit_2(self):
        original_run = subprocess.run
        calls = []

        def missing_opencc(command, **kwargs):
            if command[0] == "opencc":
                calls.append(command)
                raise FileNotFoundError("opencc 不存在")
            return original_run(command, **kwargs)

        with tempfile.TemporaryDirectory(prefix="gate-test-") as directory:
            path = Path(directory) / "deck.html"
            path.write_text("<p>成果</p>", encoding="utf-8")
            output = io.StringIO()
            with patch.object(deck_gates.subprocess, "run", side_effect=missing_opencc):
                with contextlib.redirect_stdout(output):
                    result = deck_gates.run(path, "提案")
            self.assertEqual(result, 2, output.getvalue())
            self.assertIn("工具錯誤=1 exit=2", output.getvalue())
            self.assertEqual(len(calls), 1)

    def test_question_mid_heading_nested_markup_and_entities(self):
        result = self.check("<p>內容</p>\n<h2>新手，&#22914;<span>何</span>完成任務</h2>")
        self.assertEqual(result.returncode, 1)
        self.assertIn(":2: [疑問句標題]", result.stdout)

    def test_questions_only_h1_h2_h3(self):
        result = self.check("<p>如何完成任務</p><h4>如何完成任務</h4><script>如何</script>")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_hard_wording_across_inline_tags(self):
        result = self.check("<p>拍<span>板</span></p>")
        self.assertEqual(result.returncode, 1)
        self.assertIn("[口語與俚俗] 拍板", result.stdout)

    def test_hidden_script_style_not_wording(self):
        result = self.check("<script>拍板</script><style>/* 拍板 */</style><p>完成</p>")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_auxiliary_hits_are_nonblocking(self):
        with tempfile.TemporaryDirectory() as directory:
            scanner = Path(directory) / "scanner.sh"
            scanner.write_text("echo '1:對齊'\n")
            result = self.check("<p>對齊</p>", config={
                "variants": {"提案": {}}, "auxiliary_scanners": [str(scanner)]})
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("deck.html:1:對齊", result.stdout)

    def test_signature_missing_or_forbidden(self):
        config = {"variants": {"測試變體": {"required": ["示範團隊.*成果"], "forbidden": ["禁止署名"]}}}
        for html, expected in (("<p>成果</p>", 1), ("<p>示範團隊成果</p>", 0),
                               ("<p>示範團隊成果 禁止署名</p>", 1)):
            result = self.check(html, "測試變體", config=config)
            self.assertEqual(result.returncode, expected, result.stdout)

    def test_variant_forbidden_split_by_inline_tags(self):
        config = {"variants": {"測試變體": {"forbidden": ["禁止署名"]}}}
        result = self.check("<p>成果</p>\n<p>禁止<span>署名</span></p>", "測試變體", config=config)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(":2: [署名禁止字串] 禁止署名", result.stdout)

    def test_variant_forbidden_encoded_as_entities(self):
        config = {"variants": {"測試變體": {"forbidden": ["禁止署名"]}}}
        for text in ("禁&#27490;署名", "禁&#x6b62;署名"):
            with self.subTest(text=text):
                result = self.check("<p>成果</p>\n<p>" + text + "</p>", "測試變體", config=config)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(":2: [署名禁止字串] 禁止署名", result.stdout)

    def test_variant_required_split_by_inline_tags_or_entities(self):
        config = {"variants": {"測試變體": {"required": ["示範團隊成果"]}}}
        for text in ("示範團隊<span>成果</span>", "示範團隊&#25104;果"):
            with self.subTest(text=text):
                result = self.check("<p>" + text + "</p>", "測試變體", config=config)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_variant_required_matches_raw_source(self):
        config = {"variants": {"測試變體": {"required": ['data-signature="示範團隊"']}}}
        result = self.check('<p data-signature="示範團隊">成果</p>', "測試變體", config=config)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_configs(self):
        for config in ({}, {"variants": []}, {"variants": {"提案": {"required": "["}}},
                       {"variants": {"提案": {"required": ["["]}}},
                       {"variants": {"提案": {}}, "auxiliary_scanners": "invalid"}):
            result = self.check("<p>成果</p>", config=config)
            self.assertEqual(result.returncode, 2, result.stdout)

    def test_exact_facts_positive_and_negative(self):
        facts = {"required": ["示範團隊 × 範例公司"], "forbidden": ["測試講者"]}
        good = self.check(COURSE, "課程", facts)
        self.assertEqual(good.returncode, 0, good.stdout)
        missing = self.check(COURSE.replace("範例公司", "測試公司"), "課程", facts)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("[Facts 署名缺漏]", missing.stdout)
        bad = self.check(COURSE + "<p>測試講者</p>", "課程", facts)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("[Facts 禁止字串]", bad.stdout)

    def test_forbidden_string_in_speaker_notes_blocked(self):
        result = self.check('<p>成果</p>\n\n<section data-notes="請先向測試講者確認"><p>成果</p></section>',
                            facts={"required": [], "forbidden": ["測試講者"]})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(":3: [講者備註禁止字串] 測試講者", result.stdout)
        self.assertIn("講者備註 1 則已核對", result.stdout)

    def test_speaker_notes_entities_and_case(self):
        result = self.check('<section data-notes="&#28204;試講者"></section>\n'
                            "<section data-notes='ACME 專案'></section>",
                            facts={"required": [], "forbidden": ["測試講者", "Acme"]})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(":1: [講者備註禁止字串] 測試講者", result.stdout)
        self.assertIn(":2: [講者備註禁止字串] Acme", result.stdout)
        self.assertIn("講者備註 2 則已核對", result.stdout)

    def test_speaker_notes_inside_template_checked(self):
        result = self.check('<template>\n<section data-notes="測試講者"></section>\n</template><p>成果</p>',
                            facts={"required": [], "forbidden": ["測試講者"]})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(":2: [講者備註禁止字串] 測試講者", result.stdout)

    def test_speaker_notes_without_forbidden_pass(self):
        facts = {"required": [], "forbidden": ["測試講者"]}
        result = self.check('<section data-notes="請放慢速度" title="測試講者"><p>成果</p></section>', facts=facts)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        empty = self.check('<p>成果</p>', facts=facts)
        self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
        no_facts = self.check('<section data-notes="測試講者"><p>成果</p></section>')
        self.assertEqual(no_facts.returncode, 0, no_facts.stdout + no_facts.stderr)
        self.assertIn("限制：無署名 sidecar", no_facts.stdout)
        self.assertNotIn("則已核對", no_facts.stdout)

    def test_bad_inputs_fail_closed(self):
        for variant, facts in (("未知", None), ("提案", {"required": "錯誤", "forbidden": []}), ("提案", [])):
            with self.subTest(variant=variant, facts=facts):
                result = self.check("<p>成果</p>", variant, facts)
                self.assertEqual(result.returncode, 2, result.stdout)
        missing = subprocess.run(["bash", str(GATE), "不存在.html", "提案"], capture_output=True)
        self.assertEqual(missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()

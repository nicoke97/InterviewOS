import unittest

from app.sde_content import day1_sheet_ids, load_sde, recovery_sheet_ids
from app.sde_engine import _cta_path, _norm, get_reading, weighted_sample


class SdeContentTests(unittest.TestCase):
    def test_two_sum_day1_length(self):
        data = load_sde()
        algo = data["algos"]["two-sum"]
        ids = day1_sheet_ids(algo, "csharp")
        self.assertEqual(len(ids), 17)
        self.assertTrue(ids[0].startswith("r1-"))
        self.assertIn("full-01", ids)
        self.assertNotIn("full-recall", ids)

    def test_recovery_has_three_rungs_and_full(self):
        data = load_sde()
        ids = recovery_sheet_ids(data["algos"]["two-sum"], "python")
        self.assertEqual(ids[-1], "full-recall")
        self.assertGreaterEqual(len(ids), 4)

    def test_sections_exist(self):
        data = load_sde()
        # 5 foundation (w00) sections + 16 weeks * 5 days = 85.
        self.assertEqual(len(data["sections"]), 85)
        self.assertEqual(data["first_lang"], "csharp")

    def test_theory_english_is_canonical(self):
        from app.sde_i18n import localize_section, sheet_prompt

        data = load_sde()
        sec = data["section_by_id"]["w01-big-o-s1"]
        self.assertIn("does not grow", sec["reading"])
        self.assertIn("no crece", sec["reading_es"])
        self.assertIn("does not grow", localize_section(sec, "en")["reading"])
        self.assertIn("no crece", localize_section(sec, "es")["reading"])
        sheet = data["algos"]["two-sum"]["languages"]["csharp"]["sheets"][0]
        self.assertIn("Rung", sheet_prompt(sheet, "en"))
        self.assertIn("Peldaño", sheet_prompt(sheet, "es"))

    def test_full_interview_catalog_has_day1_ladders(self):
        data = load_sde()
        order = data["algo_order"]
        self.assertEqual(len(order), 28)
        self.assertEqual(order[0], "two-sum")
        self.assertEqual(order[-1], "merge-intervals")
        for algo_id in order:
            self.assertIn(algo_id, data["algos"], algo_id)
            for lang in ("csharp", "python"):
                ids = day1_sheet_ids(data["algos"][algo_id], lang)
                self.assertEqual(len(ids), 17, f"{algo_id}/{lang}")
                sheets = {s["id"]: s for s in data["algos"][algo_id]["languages"][lang]["sheets"]}
                self.assertIn("___", sheets["r1-01"]["starter_code"], f"{algo_id}/{lang}")
                self.assertIn("___", sheets["r2-01"]["starter_code"], f"{algo_id}/{lang}")
                self.assertIn("___", sheets["r3-01"]["starter_code"], f"{algo_id}/{lang}")
                self.assertNotEqual(
                    sheets["r1-01"]["starter_code"],
                    sheets["r1-02"]["starter_code"],
                    f"{algo_id}/{lang} names should change",
                )


class SdeDebugCatalogTests(unittest.TestCase):
    def test_interview_debug_pool_loaded(self):
        data = load_sde()
        ids = [b["id"] for b in data["debug"]]
        self.assertGreaterEqual(len(ids), 18)
        self.assertEqual(len(ids), len(set(ids)))
        for required in (
            "dbg-bs-last-candidate",
            "dbg-bs-mid-overflow",
            "dbg-two-ptr-overlap",
            "dbg-window-size",
            "dbg-reverse-lost-next",
            "dbg-cycle-fast-null",
            "dbg-kadane-init",
            "dbg-nplusone-queries",
            "dbg-py-backtrack-alias",
            "dbg-py-tax-round",
        ):
            self.assertIn(required, ids)
        self.assertNotIn("dbg-off-by-one-sum", ids)
        self.assertNotIn("dbg-py-off-by-one", ids)

    def test_python_broken_snippets_fail(self):
        from app.executor import run_leetcode_code

        data = load_sde()
        for bug in data["debug"]:
            if bug.get("lang") != "python":
                continue
            res = run_leetcode_code(
                bug["broken_code"],
                bug["test_cases"],
                fn_name=bug["fn_name"],
                language="python",
            )
            self.assertFalse(res.get("passed"), bug["id"])


class SdeEngineHelpersTests(unittest.TestCase):
    def test_weighted_sample_no_dupes(self):
        items = list(range(12))
        picked = weighted_sample(items, [1] * 12, 40)
        self.assertEqual(len(picked), 12)
        self.assertEqual(len(set(picked)), 12)

    def test_voice_norm(self):
        self.assertIn("indice", _norm("índice"))
        self.assertIn("o(n)", _norm("O(n)"))

    def test_cta_follows_first_incomplete_reading(self):
        path = _cta_path([
            {"type": "reading", "week_id": "w01-big-o", "completed": False},
            {"type": "flashcards", "id": "cards"},
        ])
        self.assertEqual(path, "/sde/reading/w01-big-o")

    def test_cta_skips_completed_reading(self):
        path = _cta_path([
            {"type": "reading", "week_id": "w01-big-o", "completed": True},
            {"type": "flashcards", "id": "cards"},
        ])
        self.assertEqual(path, "/sde/cards")

    def test_reading_payload(self):
        payload = get_reading("w01-big-o", "en")
        self.assertIsNotNone(payload)
        self.assertIn("Big O", payload["title"])
        self.assertGreater(len(payload["intro"]), 40)


if __name__ == "__main__":
    unittest.main()

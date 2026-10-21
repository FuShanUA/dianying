import unittest
from pathlib import Path

from batch_completion import (
    BATCH_BASIC_FIELDS,
    BATCH_BASIC_MISSING_SQL,
    CHINESE_TEXT_FIELDS,
    EXTRA_FIELD_CONDITIONS,
    build_extra_fill_fields,
    contains_chinese,
    filter_batch_fields,
    is_empty_value,
    is_missing_value,
)


class BatchCompletionTests(unittest.TestCase):
    def test_extra_fields_follow_selected_checkboxes(self):
        fields = build_extra_fill_fields(
            fill_title_zh=True,
            fill_plot_zh=False,
            fill_plot=True,
            fill_dir_zh=False,
            fill_act_zh=True,
            fill_douban_rating=True,
        )
        self.assertEqual(
            fields, ("title_zh", "plot", "actors_zh", "douban_rating")
        )

    def test_filter_keeps_only_selected_nonempty_values(self):
        proposal = {
            "title_zh": "测试片名",
            "plot": "测试简介",
            "director_zh": "",
            "actors_zh": None,
            "douban_rating": 0,
        }
        result = filter_batch_fields(proposal, ("title_zh", "plot"))
        self.assertEqual(result, {"title_zh": "测试片名", "plot": "测试简介"})

    def test_contains_chinese_filters_untranslated_values(self):
        self.assertTrue(contains_chinese("冯小刚"))
        self.assertTrue(contains_chinese("淳于珊珊, 周里京"))
        self.assertFalse(contains_chinese("Philip Gröning"))
        self.assertFalse(contains_chinese(""))
        self.assertFalse(contains_chinese(None))

    def test_is_empty_value(self):
        self.assertTrue(is_empty_value(None))
        self.assertTrue(is_empty_value(""))
        self.assertTrue(is_empty_value(0))
        self.assertFalse(is_empty_value("1942"))
        self.assertFalse(is_empty_value(7.2))

    def test_chinese_fields_count_non_chinese_as_missing(self):
        self.assertTrue(is_missing_value("title_zh", "Sybil"))
        self.assertTrue(is_missing_value("director_zh", "Philip Gröning"))
        self.assertFalse(is_missing_value("title_zh", "爱丽丝"))
        self.assertFalse(is_missing_value("actors_zh", "淳于珊珊, 周里京"))
        self.assertTrue(is_missing_value("title_zh", ""))
        self.assertFalse(is_missing_value("year", 2009))
        self.assertTrue(is_missing_value("year", 0))
        for field, cond in EXTRA_FIELD_CONDITIONS:
            if field in CHINESE_TEXT_FIELDS:
                self.assertIn("GLOB", cond)

    def test_basic_condition_does_not_exclude_existing_ids(self):
        self.assertIn("imdb_rating", BATCH_BASIC_FIELDS)
        self.assertNotIn("tmdb_id", BATCH_BASIC_MISSING_SQL)
        self.assertNotIn("imdb_id", BATCH_BASIC_MISSING_SQL)

    def test_app_uses_the_imported_basic_field_constant(self):
        app_source = Path(__file__).with_name("app.py").read_text(encoding="utf-8")
        self.assertNotIn("BASIC_BATCH_FIELDS", app_source)
        self.assertNotIn("BATCH_UNATTEMPTED_SQL", app_source)
        self.assertNotIn("mark_batch_attempted", app_source)


if __name__ == "__main__":
    unittest.main()

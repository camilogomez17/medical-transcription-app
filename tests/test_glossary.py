"""Tests for glossary matching and safe fallback labeling."""

import unittest

from glossary import find_terms
from translation_engine import TranslationEngine


class GlossaryTests(unittest.TestCase):
    def test_matches_english_terms(self):
        self.assertIn(("chest pain", "dolor en el pecho"), find_terms("I have chest pain."))

    def test_matches_spanish_terms(self):
        self.assertIn(
            ("abdominal pain", "dolor abdominal"),
            find_terms("Tengo dolor abdominal.", source_language="es"),
        )

    def test_does_not_match_inside_unrelated_words(self):
        self.assertEqual([], find_terms("the treatment plan", source_language="es"))

    def test_missing_translation_is_labeled_as_glossary_only(self):
        engine = TranslationEngine()
        engine._translate = None
        result = engine.translate("I have chest pain", "en", "es")
        self.assertIn("GLOSSARY ONLY", result)
        self.assertIn("This is not a complete translation.", result)


if __name__ == "__main__":
    unittest.main()

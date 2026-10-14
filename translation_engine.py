"""Local translation helpers.

Argos Translate can run locally, but it still needs language packages installed.
If those packages are not present, this module returns glossary hints instead.
"""

from __future__ import annotations

from glossary import find_terms


class TranslationEngine:
    def __init__(self) -> None:
        self._translate = None
        try:
            from argostranslate import translate

            self._translate = translate
        except Exception:
            self._translate = None

    def translate(self, text: str, source: str, target: str) -> str:
        if not text.strip():
            return ""

        if self._translate is not None:
            translated = self._translate_with_argos(text, source, target)
            if translated is not None:
                return translated

        return self._glossary_fallback(text, "Local translation is not installed yet.")

    def _translate_with_argos(self, text: str, source: str, target: str) -> str | None:
        installed_languages = self._translate.get_installed_languages()
        source_language = self._find_language(installed_languages, source)
        target_language = self._find_language(installed_languages, target)

        if source_language is None or target_language is None:
            return self._glossary_fallback(
                text,
                (
                    "Local translation package is not installed yet. "
                    "Run: python install_translation_packages.py"
                ),
            )

        translation = source_language.get_translation(target_language)
        if translation is None:
            return self._glossary_fallback(
                text,
                (
                    f"Local {source}->{target} translation package is missing. "
                    "Run: python install_translation_packages.py"
                ),
            )

        try:
            return translation.translate(text)
        except Exception as exc:
            return self._glossary_fallback(text, f"Local translation failed: {exc}")

    def _find_language(self, languages, code: str):
        for language in languages:
            if language.code == code:
                return language
        return None

    def _glossary_fallback(self, text: str, reason: str) -> str:
        matches = find_terms(text)
        if not matches:
            return f"{reason}\n\nGlossary hints: no medical glossary terms found yet."

        lines = [reason, "", "Glossary hints:"]
        lines.extend(f"- {english}: {spanish}" for english, spanish in matches)
        return "\n".join(lines)

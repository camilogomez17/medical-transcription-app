"""Local translation helpers with clearly labeled glossary fallback."""

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

        if source == target:
            return text

        if self._translate is not None:
            translated = self._translate_with_argos(text, source, target)
            if translated is not None:
                return translated

        return self._glossary_fallback(
            text, source, target, "Local translation is not installed yet."
        )

    def _translate_with_argos(self, text: str, source: str, target: str) -> str | None:
        installed_languages = self._translate.get_installed_languages()
        source_language = self._find_language(installed_languages, source)
        target_language = self._find_language(installed_languages, target)

        if source_language is None or target_language is None:
            return self._glossary_fallback(
                text,
                source,
                target,
                (
                    "Local translation package is not installed yet. "
                    "Run: python install_translation_packages.py"
                ),
            )

        translation = source_language.get_translation(target_language)
        if translation is None:
            return self._glossary_fallback(
                text,
                source,
                target,
                (
                    f"Local {source}->{target} translation package is missing. "
                    "Run: python install_translation_packages.py"
                ),
            )

        try:
            return translation.translate(text)
        except Exception as exc:
            return self._glossary_fallback(
                text, source, target, f"Local translation failed: {exc}"
            )

    def _find_language(self, languages, code: str):
        for language in languages:
            if language.code == code:
                return language
        return None

    def _glossary_fallback(
        self, text: str, source: str, target: str, reason: str
    ) -> str:
        matches = find_terms(text, source)
        if not matches:
            return (
                f"[GLOSSARY ONLY — NOT A FULL TRANSLATION] {reason}\n\n"
                "No matching medical glossary terms were found. Do not use this "
                "as a complete translation."
            )

        lines = [
            f"[GLOSSARY ONLY — NOT A FULL TRANSLATION] {reason}",
            "",
            "Matching glossary terms (reference only):",
        ]
        if source == "es" and target == "en":
            lines.extend(f"- {spanish}: {english}" for english, spanish in matches)
        else:
            lines.extend(f"- {english}: {spanish}" for english, spanish in matches)
        lines.append("")
        lines.append("This is not a complete translation.")
        return "\n".join(lines)

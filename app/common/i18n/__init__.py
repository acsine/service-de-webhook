import json
import os
from typing import Dict, Any
from fastapi import Request, Header
from typing import Optional

class TranslationManager:
    def __init__(self):
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.default_locale = 'en'
        self.supported_locales = ['en', 'fr', 'es', 'ar']
        self.load_translations()

    def load_translations(self):
        """Load all translation files"""
        locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locales')

        for locale in self.supported_locales:
            file_path = os.path.join(locales_dir, f'{locale}.json')
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[locale] = json.load(f)
                print(f"Loaded translations for {locale}")
            except FileNotFoundError:
                print(f"Translation file not found for {locale}: {file_path}")
            except json.JSONDecodeError as e:
                print(f"Error parsing translation file for {locale}: {e}")

    def get_locale_from_header(self, accept_language: Optional[str] = None) -> str:
        """Extract locale from Accept-Language header"""
        if not accept_language:
            return self.default_locale

        # Parse Accept-Language header (e.g., "en-US,en;q=0.9,fr;q=0.8")
        languages = []
        for lang in accept_language.split(','):
            if ';' in lang:
                lang = lang.split(';')[0]
            lang = lang.strip().lower()[:2]  # Get first 2 characters
            if lang in self.supported_locales:
                languages.append(lang)

        return languages[0] if languages else self.default_locale

    def translate(self, key: str, locale: str = None, **kwargs) -> str:
        """
        Translate a key to the specified locale

        Args:
            key: Translation key in dot notation (e.g., 'messages.hello_world')
            locale: Target locale
            **kwargs: Variables for string formatting

        Returns:
            Translated string
        """
        if locale is None:
            locale = self.default_locale

        if locale not in self.supported_locales:
            locale = self.default_locale

        # Get translation from nested dict
        translation = self.translations.get(locale, {})
        keys = key.split('.')

        for k in keys:
            if isinstance(translation, dict) and k in translation:
                translation = translation[k]
            else:
                # Fallback to English if key not found
                fallback = self.translations.get(self.default_locale, {})
                for fk in keys:
                    if isinstance(fallback, dict) and fk in fallback:
                        fallback = fallback[fk]
                    else:
                        return key  # Return key if translation not found
                translation = fallback
                break

        if isinstance(translation, str):
            try:
                return translation.format(**kwargs)
            except KeyError:
                return translation

        return key

# Global translation manager instance
translator = TranslationManager()

def get_translator():
    """Dependency to get translator instance"""
    return translator

def get_locale_from_request(
    accept_language: Optional[str] = Header(None, alias="accept-language")
) -> str:
    """FastAPI dependency to extract locale from request headers"""
    return translator.get_locale_from_header(accept_language)

def t(key: str, locale: str = 'en', **kwargs) -> str:
    """Shorthand translation function"""
    return translator.translate(key, locale, **kwargs)

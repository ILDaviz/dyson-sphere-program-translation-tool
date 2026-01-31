import json
import os

class CacheManager:
    """
    Manages translation persistence to avoid redundant API calls.
    Supports context-aware caching (English|Context -> Translation).
    """
    def __init__(self, lang, cache_file=None):
        self.lang = lang
        self.cache_file = cache_file if cache_file else f'translation_cache_{lang}.json'
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def get(self, text, context=None):
        """
        Retrieve translation. 
        Prioritizes exact context matches (text|context), falls back to text-only legacy keys.
        """

        # Best match: Specific context
        if context:
            composite_key = f"{text}|{context}"
            if composite_key in self.cache:
                return self.cache[composite_key]

        # Backward compatibility: Legacy/Simple keys
        if text in self.cache:
            return self.cache[text]
            
        return None

    def set(self, text, translation, context=None):
        """Save translation, preferring context-aware keys."""
        if context:
            key = f"{text}|{context}"
        else:
            key = text
            
        self.cache[key] = translation

    def save(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=4)
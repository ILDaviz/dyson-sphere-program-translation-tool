import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from src.cache_manager import CacheManager
from src.openai import translate_batch, load_glossary

class TestCacheManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for cache testing
        self.test_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.test_dir, 'test_cache.json')

    def tearDown(self):
        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def test_cache_set_get(self):
        """Test simple set and get operations"""
        cache = CacheManager("it", self.cache_file)
        cache.set("Hello", "Ciao")
        
        self.assertEqual(cache.get("Hello"), "Ciao")
        self.assertIsNone(cache.get("World"))

    def test_cache_patch_scenarios(self):
        """Test specific scenarios that happen during a game patch"""
        cache = CacheManager("it", self.cache_file)
        
        # Meaning Change (Same English, Different Chinese)
        # Old version of the game had "Light" as "Luce"
        cache.set("Light", "Luce", context="光")
        # New patch uses "Light" to mean "Leggero" (Weight)
        cache.set("Light", "Leggero", context="轻")
        
        self.assertEqual(cache.get("Light", context="光"), "Luce")
        self.assertEqual(cache.get("Light", context="轻"), "Leggero")
        self.assertNotEqual(cache.get("Light", context="轻"), cache.get("Light", context="光"))

        # Backward Compatibility (Legacy Cache)
        # Imagine a cache created with the OLD version of your tool (no context)
        cache.cache["LegacyKey"] = "TraduzioneVecchia"
        
        # It should still find it even if we provide context now
        self.assertEqual(cache.get("LegacyKey", context="AnyContext"), "TraduzioneVecchia")
        self.assertEqual(cache.get("LegacyKey"), "TraduzioneVecchia")

        # New String (Cache Miss)
        self.assertIsNone(cache.get("Brand New String", context="NewContext"))

    def test_cache_persistence(self):
        """Test that cache is saved to disk and reloaded correctly"""
        # Create cache and save data
        cache1 = CacheManager("it", self.cache_file)
        cache1.set("Cat", "Gatto")
        cache1.save()

        # Reload from disk in a new instance
        cache2 = CacheManager("it", self.cache_file)
        self.assertEqual(cache2.get("Cat"), "Gatto")

class TestOpenAILogic(unittest.TestCase):
    def setUp(self):
        # Create a dummy glossary file
        with open("glossary.txt", "w") as f:
            f.write("Do not translate proper nouns.\n")

    def tearDown(self):
        # Clean up dummy glossary
        if os.path.exists("glossary.txt"):
            os.remove("glossary.txt")

    def test_load_glossary(self):
        rules = load_glossary()
        self.assertIn("Do not translate proper nouns.", rules)

    @patch('src.openai.openai.OpenAI')
    def test_translate_batch_success(self, mock_openai):
        """Test translate_batch with a mocked successful API response"""
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = json.dumps({
            "items": [
                {"id": "0", "translated_text": "Mela"},
                {"id": "1", "translated_text": "Banana"}
            ]
        })
        mock_client.chat.completions.create.return_value = mock_completion

        texts_map = {
            "0": {"text": "Apple", "context": "苹果", "len": 5},
            "1": {"text": "Banana", "context": "香蕉", "len": 6}
        }
        
        result = translate_batch(texts_map, "it", "gpt-4o-mini")

        self.assertEqual(result["0"], "Mela")
        self.assertEqual(result["1"], "Banana")
        
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], "gpt-4o-mini")
        self.assertEqual(call_args['response_format']['type'], "json_schema")
        self.assertEqual(call_args['response_format']['json_schema']['name'], "translation_response")

    @patch('src.openai.openai.OpenAI')
    def test_translate_batch_failure(self, mock_openai):
        """Test graceful handling of API errors"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        texts_map = {"0": {"text": "Apple", "context": "苹果"}}
        result = translate_batch(texts_map, "it")

        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()

from typing import Dict, Optional
import json
import os
from datetime import datetime, timedelta

class TranslationCache:
    def __init__(self, cache_file: str, ttl_days: int = 7):
        self.cache_file = cache_file
        self.ttl = timedelta(days=ttl_days)
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
        
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
            
    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            timestamp = datetime.fromisoformat(self.cache[key]['timestamp'])
            if datetime.now() - timestamp < self.ttl:
                return self.cache[key]['translation']
        return None
        
    def set(self, key: str, translation: str):
        self.cache[key] = {
            'translation': translation,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache() 
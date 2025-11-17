import json
import os
from datetime import datetime

from scraper.utils.redis_cache import cache_progress


class ScraperPipeline:

    def __init__(self):
        self.results_dir = 'media/scraping_results'
        os.makedirs(self.results_dir, exist_ok=True)

    def process_item(self, item, spider):
        try:
            if 'timestamp' not in item:
                item['timestamp'] = datetime.now().timestamp()

            session_id = item.get('session_id', 'unknown')
            result_file = os.path.join(self.results_dir, f"{session_id}_results.json")

            existing_results = []
            if os.path.exists(result_file):
                try:
                    with open(result_file, 'r') as f:
                        existing_results = json.load(f)
                except:
                    existing_results = []

            existing_results.append(dict(item))

            with open(result_file, 'w') as f:
                json.dump(existing_results, f, indent=2, ensure_ascii=False)

            spider.logger.info(f"Item salvo: {item.get('url', 'N/A')}")
            cache_progress(session_id, {
                'type': 'screenshot',
                'message': 'Resultado salvo',
                'stage': 'item_saved',
                'session_id': session_id,
                'screenshot_path': item.get('screenshot_path'),
                'url': item.get('url'),
                'status': 'success'
            })

        except Exception as e:
            spider.logger.error(f"Erro no pipeline: {e}")

        return item

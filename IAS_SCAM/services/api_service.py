import requests
import json
import os
from PyQt6.QtCore import QThread, pyqtSignal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_app_data_dir():
    app_name = "IAS_SCAM"
    if os.name == 'nt':
        base = os.getenv('APPDATA') or os.path.expanduser("~")
        return os.path.join(base, app_name)
    return os.path.join(os.path.expanduser("~"), f".{app_name.lower()}")

CACHE_DIR = get_app_data_dir()
os.makedirs(CACHE_DIR, exist_ok=True)

CACHE_FILE = os.path.join(CACHE_DIR, "geo_cache.json")
ADDRESS_CACHE_FILE = os.path.join(CACHE_DIR, "address_cache.json")

def load_geo_cache():
    """Зчитує локальний кеш назв вулиць для прискорення автозаповнення."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Помилка читання geo_cache: {e}")
    return {}


def save_geo_cache(cache_data):
    """Записує верифіковані назви вулиць у локальний кеш json."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Помилка збереження geo_cache: {e}")


def load_address_cache():
    """Завантажує точний кеш координат будинків (вулиця + номер будинку) для карти."""
    if os.path.exists(ADDRESS_CACHE_FILE):
        try:
            with open(ADDRESS_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Помилка читання address_cache: {e}")
    return {}


def save_address_cache(cache_data):
    """Фіксує нові знайдені геокоординати будинків у кеш-файл."""
    try:
        with open(ADDRESS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Помилка збереження address_cache: {e}")


class AddressSearchThread(QThread):
    """Асинхронний фоновий потік пошуку та валідації адрес через OpenStreetMap Nominatim API."""
    results_ready = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.query = ""

    def search(self, query):
        """Конфігурує новий пошуковий рядок та запускає фоновий робочий потік."""
        self.query = query.strip()
        self.start()

    def run(self):
        if len(self.query) < 3: 
            self.results_ready.emit([])
            return
            
        print(f"🔍 Шукаю адресу: {self.query}")
        
        cache = load_geo_cache()
        query_words = [w for w in self.query.lower().replace(',', ' ').split() if len(w) > 2]
        
        if query_words:
            local_matches = []
            for cached_street in cache.keys():
                if all(word in cached_street for word in query_words):
                    formatted_street = " ".join(w.capitalize() for w in cached_street.split())
                    local_matches.append(formatted_street)
            
            if local_matches:
                print(f"⚡ Знайдено в локальному кеші: {local_matches}")
                self.results_ready.emit(local_matches[:8])
                return 
        
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={self.query}, Київ&format=json&addressdetails=1&limit=8"
            headers = {'User-Agent': 'SkamCommunalApp/1.1'}
            response = requests.get(url, headers=headers, timeout=4)
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    self.results_ready.emit([])
                    return

                results = []
                cache_updated = False
                
                for item in data:
                    osm_class = item.get('class', '')
                    if osm_class not in ['highway', 'building', 'place']:
                        continue

                    addr = item.get('address', {})
                    road = addr.get('road', '')
                    lat = float(item.get('lat', 0))
                    lon = float(item.get('lon', 0))
                    
                    if road:
                        res = f"{road}"
                        res_lower = res.lower()
                        is_relevant = False
                        
                        if not query_words:
                            is_relevant = True
                        else:
                            for word in query_words:
                                if word in res_lower:
                                    is_relevant = True
                                    break
                        
                        if is_relevant and res not in results:
                            results.append(res)
                            if res_lower not in cache:
                                cache[res_lower] = [lat, lon]
                                cache_updated = True
                
                if cache_updated:
                    save_geo_cache(cache)
                    
                self.results_ready.emit(results)
            else:
                self.results_ready.emit([])
        except Exception as e:
            print(f"Критична помилка API адрес: {e}")
            self.results_ready.emit([])
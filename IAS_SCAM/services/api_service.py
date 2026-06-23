# services/api_service.py
import requests
import json
import os
from PyQt6.QtCore import QThread, pyqtSignal

CACHE_FILE = "geo_cache.json"

def load_geo_cache():
    """Завантажує кеш адрес та їхніх координат."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Помилка читання кешу: {e}")
    return {}

def save_geo_cache(cache_data):
    """Зберігає оновлений кеш у файл."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Помилка збереження кешу: {e}")

class AddressSearchThread(QThread):
    results_ready = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.query = ""

    def search(self, query):
        self.query = query
        self.start()

    def run(self):
        if len(self.query) < 3: 
            self.results_ready.emit([])
            return
            
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={self.query}, Київ&format=json&addressdetails=1&limit=8"
            headers = {'User-Agent': 'SkamCommunalApp/1.1'}
            response = requests.get(url, headers=headers, timeout=4)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Завантажуємо поточний кеш
                cache = load_geo_cache()
                cache_updated = False
                
                for item in data:
                    addr = item.get('address', {})
                    road = addr.get('road', '')
                    house = addr.get('house_number', '') or addr.get('building', '')
                    lat = float(item.get('lat', 0))
                    lon = float(item.get('lon', 0))
                    
                    if road:
                        res = f"{road}"
                        if house: res += f", {house}"
                        
                        if res not in results:
                            results.append(res)
                            
                            # Додаємо адресу з координатами в словник, якщо її там ще немає
                            cache_key = res.lower()
                            if cache_key not in cache:
                                cache[cache_key] = [lat, lon]
                                cache_updated = True
                
                # Зберігаємо файл, якщо знайшли нові адреси
                if cache_updated:
                    save_geo_cache(cache)
                    
                self.results_ready.emit(results)
            else:
                self.results_ready.emit([])
        except Exception as e:
            print(f"Помилка API адрес: {e}")
            self.results_ready.emit([])
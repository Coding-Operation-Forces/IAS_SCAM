# services/api_service.py
import requests
import json
import os
from PyQt6.QtCore import QThread, pyqtSignal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "geo_cache.json")

def load_geo_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Помилка читання кешу: {e}")
    else:
        print(f"⚠️ Файл кешу не знайдено за шляхом: {CACHE_FILE}. Створимо новий.")
    return {}

def save_geo_cache(cache_data):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
        print(f"✅ Кеш успішно оновлено! Тепер у базі {len(cache_data)} адрес.")
    except Exception as e:
        print(f"❌ Помилка збереження кешу: {e}")

class AddressSearchThread(QThread):
    results_ready = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.query = ""

    def search(self, query):
        self.query = query.strip()
        self.start()

    def run(self):
        if len(self.query) < 3: 
            self.results_ready.emit([])
            return
            
        print(f"🔍 Шукаю адресу: {self.query}")
        
        # --- НОВИЙ БЛОК: ШВИДКИЙ ПОШУК ПО ЛОКАЛЬНОМУ КЕШУ ---
        cache = load_geo_cache()
        # Розбиваємо введений запит на окремі слова (наприклад, "Іваш")
        query_words = [w for w in self.query.lower().replace(',', ' ').split() if len(w) > 2]
        
        if query_words:
            local_matches = []
            for cached_street in cache.keys():
                # Перевіряємо, чи всі введені слова є в назві вулиці з кешу
                if all(word in cached_street for word in query_words):
                    # Робимо кожне слово з великої літери для краси (вулиця ярослава івашкевича -> Вулиця Ярослава Івашкевича)
                    formatted_street = " ".join(w.capitalize() for w in cached_street.split())
                    local_matches.append(formatted_street)
            
            # Якщо знайшли збіги в локальному файлі — миттєво віддаємо їх і ЗУПИНЯЄМОСЬ!
            if local_matches:
                print(f"⚡ Знайдено в локальному кеші: {local_matches}")
                self.results_ready.emit(local_matches[:8])
                return 
        # ----------------------------------------------------
        
        # Якщо в кеші нічого не знайшли — йдемо в інтернет
        try:
            url = f"https://nominatim.openstreetmap.org/search?q={self.query}, Київ&format=json&addressdetails=1&limit=8"
            headers = {'User-Agent': 'SkamCommunalApp/1.1'}
            response = requests.get(url, headers=headers, timeout=4)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data:
                    print(f"⚠️ OpenStreetMap нічого не знайшов для запиту: {self.query}")
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
                            
                            # Зберігаємо в кеш
                            if res_lower not in cache:
                                cache[res_lower] = [lat, lon]
                                cache_updated = True
                
                if cache_updated:
                    save_geo_cache(cache)
                    
                self.results_ready.emit(results)
            else:
                print(f"❌ Помилка API. Код статусу: {response.status_code}")
                self.results_ready.emit([])
        except Exception as e:
            print(f"❌ Критична помилка API адрес: {e}")
            self.results_ready.emit([])
# services/api_service.py
import requests
from PyQt6.QtCore import QThread, pyqtSignal

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
            # Трохи змінюємо запит для кращого пошуку по Києву
            url = f"https://nominatim.openstreetmap.org/search?q={self.query}, Київ&format=json&addressdetails=1&limit=8"
            headers = {'User-Agent': 'SkamCommunalApp/1.1'}
            response = requests.get(url, headers=headers, timeout=4)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data:
                    addr = item.get('address', {})
                    road = addr.get('road', '')
                    # Шукаємо номер будинку в різних полях, які може повернути OSM
                    house = addr.get('house_number', '') or addr.get('building', '')
                    
                    if road:
                        res = f"{road}"
                        if house: res += f", {house}"
                        if res not in results:
                            results.append(res)
                
                self.results_ready.emit(results)
            else:
                self.results_ready.emit([])
        except Exception as e:
            print(f"Помилка API адрес: {e}")
            self.results_ready.emit([])
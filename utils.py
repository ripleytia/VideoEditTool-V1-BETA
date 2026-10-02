import sys
import os

def get_resource_path(relative_path):
    """
    PyInstaller ile derlendiğinde (sys._MEIPASS) veya normal çalıştırıldığında
    dosya yollarını dinamik olarak doğru bulan yardımcı fonksiyon.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller temp klasörü
        base_path = sys._MEIPASS
    else:
        # Geliştirme ortamı (main.py'nin bulunduğu dizin)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        
    return os.path.join(base_path, relative_path)

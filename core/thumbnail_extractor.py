import os
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

class ThumbnailExtractor(QThread):
    # Emits (index, pixmap) when a thumbnail is ready
    thumbnail_ready = pyqtSignal(int, QPixmap)
    finished_extraction = pyqtSignal()

    def __init__(self, video_path, duration, num_thumbnails=10):
        super().__init__()
        self.video_path = video_path
        self.duration = duration
        self.num_thumbnails = num_thumbnails
        self._is_running = True
        
        # Geçici dosyalar için sistem klasörü
        import tempfile
        self.temp_dir = os.path.join(tempfile.gettempdir(), "ripleytia_thumbs")
        os.makedirs(self.temp_dir, exist_ok=True)

    def run(self):
        if self.duration <= 0:
            self.finished_extraction.emit()
            return
            
        step = self.duration / self.num_thumbnails
        
        for i in range(self.num_thumbnails):
            if not self._is_running:
                break
                
            time_pos = i * step
            out_file = os.path.join(self.temp_dir, f"thumb_{i}.jpg")
            
            # Hızlı arama (fast seek) için -ss'i -i'den önce koyuyoruz
            # Boyutu küçük tutarak (örn. yatay 160px) işlemi hızlandırıyoruz
            cmd = [
                "ffmpeg", "-y", 
                "-ss", str(time_pos), 
                "-i", self.video_path, 
                "-vframes", "1", 
                "-q:v", "5", 
                "-s", "160x90", # Küçük çözünürlük, en boy oranını zorlamaz, sığdırır
                out_file
            ]
            
            try:
                subprocess.run(
                    cmd, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL, 
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if os.path.exists(out_file) and self._is_running:
                    pixmap = QPixmap(out_file)
                    self.thumbnail_ready.emit(i, pixmap)
            except Exception as e:
                print(f"Thumbnail çıkarma hatası: {e}")
                
        self.finished_extraction.emit()

    def stop(self):
        self._is_running = False

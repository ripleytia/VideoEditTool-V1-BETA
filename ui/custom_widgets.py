from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSlider
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

class DoubleSlider(QWidget):
    rangeChanged = pyqtSignal(int, int)

    def __init__(self, min_val=0, max_val=100):
        super().__init__()
        self.setMinimumHeight(60) # Thumbnail'lar için yüksekliği artırdık
        self._min = min_val
        self._max = max_val
        self._lower = min_val
        self._upper = max_val
        self.handle_width = 12
        self.active_handle = None
        self.thumbnails = {} # {index: QPixmap}

    def set_thumbnail(self, index, pixmap):
        self.thumbnails[index] = pixmap
        self.update()

    def clear_thumbnails(self):
        self.thumbnails.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        
        # Track boyutları
        track_height = 40
        track_y = int(height/2 - track_height/2)
        
        # Arka plan (Film Şeridi Çerçevesi)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1E1E24"))
        painter.drawRoundedRect(self.handle_width, track_y, width - self.handle_width * 2, track_height, 4, 4)

        # Thumbnail (Kareleri) Çiz
        if self.thumbnails:
            num_thumbs = max(10, len(self.thumbnails)) # Varsayılan 10 parça
            thumb_w = (width - self.handle_width * 2) / num_thumbs
            
            painter.setClipRect(self.handle_width, track_y, width - self.handle_width * 2, track_height)
            for i in range(num_thumbs):
                if i in self.thumbnails:
                    pix = self.thumbnails[i]
                    # Resmi kırparak/ölçekleyerek çiz
                    scaled_pix = pix.scaled(int(thumb_w) + 1, track_height, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    
                    x_pos = self.handle_width + int(i * thumb_w)
                    # Resmin ortasını hizala
                    y_offset = (scaled_pix.height() - track_height) // 2
                    painter.drawPixmap(x_pos, track_y, scaled_pix, 0, y_offset, int(thumb_w) + 1, track_height)
            
            painter.setClipping(False)

        # Üzerine hafif bir karartma (Opsiyonel)
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.drawRoundedRect(self.handle_width, track_y, width - self.handle_width * 2, track_height, 4, 4)

        # Handle Pozisyonlarını Hesapla
        range_span = self._max - self._min
        if range_span == 0: return

        x_lower = int((self._lower - self._min) / range_span * (width - self.handle_width * 2)) + self.handle_width
        x_upper = int((self._upper - self._min) / range_span * (width - self.handle_width * 2)) + self.handle_width

        # Aktif Seçili Alan (Kesilecek Bölüm)
        # Film şeridinin seçili kısmı aydınlık kalsın diye karartmanın üzerine sadece seçili alanı şeffaf bir morla veya parlak renkle çizebiliriz.
        painter.setBrush(QColor(157, 78, 221, 100)) # Yarı saydam Gotik Mor
        painter.drawRect(x_lower, track_y, x_upper - x_lower, track_height)
        
        # Seçili alanın üstüne ve altına mor çizgi (Vurgu)
        painter.setPen(QPen(QColor("#9D4EDD"), 2))
        painter.drawLine(x_lower, track_y, x_upper, track_y)
        painter.drawLine(x_lower, track_y + track_height, x_upper, track_y + track_height)
        painter.setPen(Qt.PenStyle.NoPen)

        # Kollar (Handles)
        painter.setBrush(QColor("#E0E0E0"))
        
        # Sol Kol
        painter.drawRoundedRect(x_lower - self.handle_width, track_y - 2, self.handle_width * 2, track_height + 4, 3, 3)
        # Sağ Kol
        painter.drawRoundedRect(x_upper - self.handle_width, track_y - 2, self.handle_width * 2, track_height + 4, 3, 3)
        
        # Kol üzerindeki çizgi detayları (Grip)
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawLine(x_lower, track_y + 10, x_lower, track_y + track_height - 10)
        painter.drawLine(x_upper, track_y + 10, x_upper, track_y + track_height - 10)

    def mousePressEvent(self, event):
        x = event.position().x()
        width = self.width()
        range_span = self._max - self._min
        
        x_lower = int((self._lower - self._min) / range_span * (width - self.handle_width * 2)) + self.handle_width
        x_upper = int((self._upper - self._min) / range_span * (width - self.handle_width * 2)) + self.handle_width

        if abs(x - x_lower) < 15:
            self.active_handle = 'lower'
        elif abs(x - x_upper) < 15:
            self.active_handle = 'upper'
        else:
            self.active_handle = None

    def mouseMoveEvent(self, event):
        if not self.active_handle:
            return

        x = event.position().x()
        width = self.width()
        
        # Map x to value
        val = self._min + (x - self.handle_width) / (width - self.handle_width * 2) * (self._max - self._min)
        val = max(self._min, min(self._max, int(val)))

        if self.active_handle == 'lower':
            if val < self._upper:
                self._lower = val
        elif self.active_handle == 'upper':
            if val > self._lower:
                self._upper = val

        self.rangeChanged.emit(self._lower, self._upper)
        self.update()

    def mouseReleaseEvent(self, event):
        self.active_handle = None

    def setMaximum(self, max_val):
        self._max = max_val
        self._upper = max_val
        self.update()

    def setRange(self, lower, upper):
        self._lower = max(self._min, lower)
        self._upper = min(self._max, upper)
        self.update()

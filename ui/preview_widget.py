import os
import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor
from PyQt6.QtCore import Qt, QRect, QPoint

class VideoPreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.layout = QVBoxLayout(self)
        
        self.image_label = QLabel("Video Önizleme Yükleniyor...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #0d0d12; border: 1px solid #333; border-radius: 8px;")
        
        self.layout.addWidget(self.image_label)
        self.layout.setContentsMargins(0,0,0,0)

        self.current_frame_path = None
        self.target_aspect_ratio = None # e.g., (16, 9)
        self.original_pixmap = None
        
        # Manuel Crop Değişkenleri
        self.is_manual_crop = False
        self.manual_crop_rect = None # Gösterilen alan üzerindeki QRect
        self._drawing = False
        self._start_pos = None
        self._end_pos = None

    def load_video_frame(self, video_path):
        from utils import get_resource_path
        # PyInstaller'da geçici dosyalar için sys._MEIPASS salt okunur olabilir, 
        # bu yüzden geçici dosyayı direkt temp klasörüne veya geçerli çalışma dizinine yazmalıyız.
        import tempfile
        temp_img_path = os.path.join(tempfile.gettempdir(), "ripleytia_temp_preview.jpg")
        cmd = [
            "ffmpeg", "-y", "-i", video_path, 
            "-ss", "00:00:01.000", "-vframes", "1", 
            temp_img_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        
        if os.path.exists(temp_img_path):
            self.current_frame_path = temp_img_path
            self.original_pixmap = QPixmap(temp_img_path)
            self.manual_crop_rect = None # Sıfırla
            self.update_preview()

    def set_target_resolution(self, width, height, is_manual=False):
        self.target_aspect_ratio = (width, height) if width and height else None
        self.is_manual_crop = is_manual
        
        # Manuel seçildiğinde imleci artı yap
        if self.is_manual_crop:
            self.image_label.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.image_label.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.manual_crop_rect = None
            
        self.update_preview()

    def update_preview(self):
        if not self.original_pixmap or self.original_pixmap.isNull():
            return
            
        label_w = self.image_label.width()
        label_h = self.image_label.height()
        
        scaled_pixmap = self.original_pixmap.scaled(
            label_w, label_h, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Ekranda çizilen resmin sol üst köşesini bul (Ortalanmış olduğu için)
        pix_w = scaled_pixmap.width()
        pix_h = scaled_pixmap.height()
        offset_x = (label_w - pix_w) // 2
        offset_y = (label_h - pix_h) // 2

        result_pixmap = QPixmap(label_w, label_h)
        result_pixmap.fill(QColor("#0d0d12"))
        
        painter = QPainter(result_pixmap)
        painter.drawPixmap(offset_x, offset_y, scaled_pixmap)
        
        # --- MANUEL CROP ÇİZİMİ ---
        if self.is_manual_crop:
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.setPen(Qt.PenStyle.NoPen)
            
            if self.manual_crop_rect:
                # Dışarıyı karart
                r = self.manual_crop_rect
                painter.drawRect(offset_x, offset_y, pix_w, r.top() - offset_y) # Üst
                painter.drawRect(offset_x, r.bottom(), pix_w, (offset_y + pix_h) - r.bottom()) # Alt
                painter.drawRect(offset_x, r.top(), r.left() - offset_x, r.height()) # Sol
                painter.drawRect(r.right(), r.top(), (offset_x + pix_w) - r.right(), r.height()) # Sağ
                
                # Çerçeve
                painter.setPen(QPen(QColor("#9D4EDD"), 2, Qt.PenStyle.DashLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(r)
            elif self._drawing and self._start_pos and self._end_pos:
                rect = QRect(self._start_pos, self._end_pos).normalized()
                painter.setPen(QPen(QColor("#B100E8"), 2))
                painter.setBrush(QColor(157, 78, 221, 50))
                painter.drawRect(rect)
            else:
                # Henüz çizilmediyse tüm resmi hafif karart ve ortada "Çizin" uyarısı ver
                painter.drawRect(offset_x, offset_y, pix_w, pix_h)
                painter.setPen(QColor("white"))
                painter.drawText(result_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Manuel Kırpma: Fareyle Alan Çizin")

        # --- OTOMATİK ASPECT RATIO SİMÜLASYONU (CROP TO FILL) ---
        elif self.target_aspect_ratio:
            tw, th = self.target_aspect_ratio
            target_ratio = tw / th
            current_ratio = pix_w / pix_h
            
            # Crop to Fill mantığı: Görüntü ekrana sığdırıldığında dışarı taşan kısımları keseceğiz.
            if current_ratio > target_ratio:
                # Orijinal daha geniş (Örn: 16:9 videoyu 9:16 yapmak). Yanlardan kırpılacak.
                box_w = pix_h * target_ratio
                box_h = pix_h
            else:
                # Orijinal daha uzun (Örn: 9:16 videoyu 16:9 yapmak). Üstten ve alttan kırpılacak.
                box_w = pix_w
                box_h = pix_w / target_ratio
                
            x = offset_x + (pix_w - box_w) / 2
            y = offset_y + (pix_h - box_h) / 2
            
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.setPen(Qt.PenStyle.NoPen)
            # Dışarıda kalanları karart (Kesilecek alanlar)
            painter.drawRect(offset_x, offset_y, int(x - offset_x), pix_h) # Sol
            painter.drawRect(int(x + box_w), offset_y, int((offset_x + pix_w) - (x+box_w)), pix_h) # Sağ
            painter.drawRect(offset_x, offset_y, pix_w, int(y - offset_y)) # Üst
            painter.drawRect(offset_x, int(y + box_h), pix_w, int((offset_y + pix_h) - (y+box_h))) # Alt
            
            # Merkeze odaklanacak alanı (Fill Area) çerçeve içine al
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#9D4EDD"), 3))
            painter.drawRect(int(x), int(y), int(box_w), int(box_h))

        painter.end()
        self.image_label.setPixmap(result_pixmap)

    # Mouse Events for Manual Cropping
    def mousePressEvent(self, event):
        if self.is_manual_crop and event.button() == Qt.MouseButton.LeftButton:
            self._drawing = True
            self._start_pos = event.position().toPoint()
            self._end_pos = self._start_pos
            self.update_preview()

    def mouseMoveEvent(self, event):
        if self.is_manual_crop and self._drawing:
            self._end_pos = event.position().toPoint()
            self.update_preview()

    def mouseReleaseEvent(self, event):
        if self.is_manual_crop and event.button() == Qt.MouseButton.LeftButton:
            self._drawing = False
            self._end_pos = event.position().toPoint()
            self.manual_crop_rect = QRect(self._start_pos, self._end_pos).normalized()
            self.update_preview()

    def get_manual_crop_data(self):
        # Gerçek video çözünürlüğüne göre oranlayıp (X, Y, W, H) döndürür
        if not self.is_manual_crop or not self.manual_crop_rect or not self.original_pixmap:
            return None
            
        label_w = self.image_label.width()
        label_h = self.image_label.height()
        
        scaled_pixmap = self.original_pixmap.scaled(
            label_w, label_h, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        pix_w = scaled_pixmap.width()
        pix_h = scaled_pixmap.height()
        offset_x = (label_w - pix_w) // 2
        offset_y = (label_h - pix_h) // 2
        
        orig_w = self.original_pixmap.width()
        orig_h = self.original_pixmap.height()
        
        r = self.manual_crop_rect
        
        # Pixmap üzerindeki sınırları aşmaması için kontrol et
        crop_x = max(0, r.left() - offset_x)
        crop_y = max(0, r.top() - offset_y)
        crop_w = min(pix_w - crop_x, r.width())
        crop_h = min(pix_h - crop_y, r.height())
        
        # Orijinal çözünürlüğe oranla
        scale_ratio_x = orig_w / pix_w
        scale_ratio_y = orig_h / pix_h
        
        real_x = int(crop_x * scale_ratio_x)
        real_y = int(crop_y * scale_ratio_y)
        real_w = int(crop_w * scale_ratio_x)
        real_h = int(crop_h * scale_ratio_y)
        
        return (real_w, real_h, real_x, real_y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.manual_crop_rect = None # Ekran boyutu değişirse kırpmayı sıfırla
        self.update_preview()

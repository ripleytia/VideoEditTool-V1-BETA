import os
import subprocess
import re
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QFileDialog, QProgressBar, QTextEdit,
    QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from ui.preview_widget import VideoPreviewWidget
from ui.custom_widgets import DoubleSlider

class DropZone(QWidget):
    file_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        
        layout = QVBoxLayout()
        self.label = QLabel("Videonuzu Buraya Sürükleyin veya Seçmek İçin Tıklayın")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.file_dropped.emit(file_path)

    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(self, "Video Seç", "", "Video Dosyaları (*.mp4 *.avi *.mov *.mkv)")
        if file_path:
            self.file_dropped.emit(file_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ripleytia Video Suite - Profesyonel")
        self.resize(1100, 750)
        
        # Stil tanımlamalarını güçlendirelim (Kısmi olarak, asıl qss main.py'dan gelecek)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # -- SOL PANEL (Önizleme ve Timeline) --
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)

        # Üst Logo/Başlık
        logo_layout = QHBoxLayout()
        logo_icon = QLabel()
        from utils import get_resource_path
        icon_path = get_resource_path(os.path.join("assets", "ripleytia_r_logo.jpg"))
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_icon.setPixmap(pixmap)
        
        title_label = QLabel("RIPLEYTIA VIDEO SUITE")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #9D4EDD; letter-spacing: 2px;")
        
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(title_label)
        logo_layout.addStretch()
        left_layout.addLayout(logo_layout)

        # Önizleme Alanı
        self.preview_widget = VideoPreviewWidget()
        left_layout.addWidget(self.preview_widget, stretch=4)
        
        # Timeline / Kesme Alanı
        timeline_group = QWidget()
        timeline_layout = QVBoxLayout(timeline_group)
        timeline_layout.setContentsMargins(0, 10, 0, 0)
        
        self.timeline_info = QLabel("Kesme Alanı (Tüm Video Seçili)")
        self.timeline_info.setStyleSheet("color: #a0a0a0;")
        timeline_layout.addWidget(self.timeline_info)
        
        self.timeline_slider = DoubleSlider(0, 100)
        self.timeline_slider.setEnabled(False)
        self.timeline_slider.rangeChanged.connect(self.on_timeline_changed)
        timeline_layout.addWidget(self.timeline_slider)
        
        left_layout.addWidget(timeline_group, stretch=1)

        # -- SAĞ PANEL (Denetim Masası / Inspector) --
        right_panel = QFrame()
        right_panel.setObjectName("InspectorPanel")
        right_panel.setFixedWidth(350)
        right_panel.setStyleSheet("#InspectorPanel { background-color: #1a1a24; border-radius: 10px; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)

        # Sürükle Bırak Alanı
        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self.on_file_selected)
        right_layout.addWidget(self.drop_zone)

        # Ayarlar Başlığı
        settings_label = QLabel("DIŞA AKTARMA AYARLARI")
        settings_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0; margin-top: 10px;")
        right_layout.addWidget(settings_label)

        # Çözünürlük Presetleri
        right_layout.addWidget(QLabel("Çözünürlük ve Format:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "TikTok / Reels (1080x1920) - 9:16",
            "YouTube HD (1920x1080) - 16:9",
            "Oyun 2K (2560x1440) - 16:9",
            "Sinema 4K (3840x2160) - 16:9",
            "Manuel (Fareyle Serbest Kırpma)"
        ])
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        right_layout.addWidget(self.preset_combo)

        # Donanım Hızlandırma Seçimi
        right_layout.addWidget(QLabel("Render Motoru:"))
        self.hw_combo = QComboBox()
        self.hw_combo.addItems([
            "Yazılım (CPU - Yüksek Kalite)",
            "NVIDIA NVENC (GPU Hızlandırma)",
            "AMD AMF (GPU Hızlandırma)"
        ])
        right_layout.addWidget(self.hw_combo)

        # Görsel Efektler Başlığı
        effects_label = QLabel("GÖRSEL EFEKTLER")
        effects_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0; margin-top: 15px;")
        right_layout.addWidget(effects_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Orijinal (Filtre Yok)",
            "Sinematik (Kontrast+)",
            "Canlı (Doygunluk+)",
            "Siyah Beyaz",
            "Vintage (Sepya)",
            "Matrix (Soğuk/Yeşil)",
            "Güneşli (Sıcak/Turuncu)",
            "Bulanık (Dream Glow)"
        ])
        right_layout.addWidget(self.filter_combo)

        # Ekstralar Başlığı
        extras_label = QLabel("EKSTRALAR")
        extras_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0; margin-top: 15px;")
        right_layout.addWidget(extras_label)

        from PyQt6.QtWidgets import QCheckBox
        self.watermark_cb = QCheckBox("Ripleytia Filigranı Ekle (Sağ Alt)")
        right_layout.addWidget(self.watermark_cb)
        
        self.mute_cb = QCheckBox("Sesi Kapat (Mute)")
        right_layout.addWidget(self.mute_cb)

        right_layout.addStretch()

        # İlerleme ve İşlem
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        right_layout.addWidget(self.progress_bar)

        self.process_btn = QPushButton("R E N D E R")
        self.process_btn.setObjectName("RenderBtn")
        self.process_btn.setMinimumHeight(45)
        self.process_btn.setStyleSheet("""
            #RenderBtn {
                background-color: #9D4EDD; font-size: 16px; letter-spacing: 2px;
            }
            #RenderBtn:hover { background-color: #B100E8; }
            #RenderBtn:disabled { background-color: #4a3b52; color: #888; }
        """)
        self.process_btn.setEnabled(False)
        right_layout.addWidget(self.process_btn)

        # Log Penceresi (Minik)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(100)
        self.log_output.hide()
        right_layout.addWidget(self.log_output)

        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addWidget(right_panel, stretch=1)

        self.selected_file = None
        self.video_duration = 0 # Saniye cinsinden

    def on_file_selected(self, file_path):
        self.selected_file = file_path
        self.process_btn.setEnabled(True)
        self.log_output.append(f"[*] Dosya: {os.path.basename(file_path)}")
        self.log_output.show()
        
        # Önizleme yükle
        self.preview_widget.load_video_frame(file_path)
        self.on_preset_changed() # Aspect ratio güncelle
        
        # Süreyi FFprobe ile al
        self.video_duration = self.get_video_duration(file_path)
        if self.video_duration > 0:
            self.timeline_slider.setEnabled(True)
            self.timeline_slider.setMaximum(int(self.video_duration))
            self.on_timeline_changed(0, int(self.video_duration))
            
            # Film şeridini temizle ve yenilerini çekmeye başla
            self.timeline_slider.clear_thumbnails()
            
            from core.thumbnail_extractor import ThumbnailExtractor
            # Önceki worker varsa durdur
            if hasattr(self, 'thumb_worker') and self.thumb_worker.isRunning():
                self.thumb_worker.stop()
                
            self.thumb_worker = ThumbnailExtractor(file_path, self.video_duration, num_thumbnails=10)
            self.thumb_worker.thumbnail_ready.connect(self.timeline_slider.set_thumbnail)
            self.thumb_worker.start()
        else:
            self.timeline_slider.setMaximum(100)
            self.timeline_slider.setEnabled(False)
            self.timeline_info.setText("Süre alınamadı. (Tüm video işlenecek)")

    def get_video_duration(self, file_path):
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return float(result.stdout.strip())
        except:
            return 0

    def on_preset_changed(self):
        idx = self.preset_combo.currentIndex()
        if idx == 0:
            self.preview_widget.set_target_resolution(9, 16, is_manual=False)
        elif idx == 4: # Manuel
            self.preview_widget.set_target_resolution(None, None, is_manual=True)
            self.timeline_info.setText("Manuel Kırpma: Önizleme ekranında fareyle bir alan çizin.")
        else:
            self.preview_widget.set_target_resolution(16, 9, is_manual=False)

    def on_timeline_changed(self, lower, upper):
        if self.video_duration > 0:
            self.timeline_info.setText(f"Kesme Alanı: {lower}s - {upper}s (Toplam: {upper - lower}s)")

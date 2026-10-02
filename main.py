import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from core.ffmpeg_handler import FFmpegWorker
from utils import get_resource_path

class App(MainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.process_btn.clicked.connect(self.start_processing)
        
        # Stilleri Yükle
        self.load_styles()

    def load_styles(self):
        style_path = get_resource_path(os.path.join("styles", "gothic_purple.qss"))
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            self.log_output.append("Uyarı: qss dosyası bulunamadı.")

    def start_processing(self):
        if not self.selected_file:
            return

        output_file = os.path.splitext(self.selected_file)[0] + "_resized.mp4"
        preset_idx = self.preset_combo.currentIndex()
        hw_idx = self.hw_combo.currentIndex()
        filter_idx = self.filter_combo.currentIndex()
        add_watermark = self.watermark_cb.isChecked()
        mute_audio = self.mute_cb.isChecked()
        
        start_time = None
        end_time = None
        
        if self.video_duration > 0:
            start_time = self.timeline_slider._lower
            end_time = self.timeline_slider._upper

        manual_crop_data = None
        if preset_idx == 4: # Manuel
            manual_crop_data = self.preview_widget.get_manual_crop_data()
            if not manual_crop_data:
                QMessageBox.warning(self, "Uyarı", "Manuel kırpma seçildi ancak alan çizilmedi. Orijinal boyut kullanılacak.")

        self.process_btn.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0) # Belirsiz ilerleme
        
        self.worker = FFmpegWorker(
            self.selected_file, output_file, preset_idx, hw_idx, 
            start_time, end_time, filter_idx, add_watermark, mute_audio, manual_crop_data
        )
        self.worker.log_updated.connect(self.log_output.append)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.start()

    def on_process_finished(self, success, message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        self.process_btn.setEnabled(True)
        self.log_output.append(f"\n[!!!] {message}")
        
        if success:
            QMessageBox.information(self, "Başarılı", message)
        else:
            QMessageBox.critical(self, "Hata", message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # İkon ayarı
    icon_path = get_resource_path(os.path.join("assets", "ripleytia_r_logo.jpg"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = App()
    window.show()
    sys.exit(app.exec())

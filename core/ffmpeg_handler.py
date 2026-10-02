import subprocess
import os
import re
from PyQt6.QtCore import QThread, pyqtSignal

class FFmpegWorker(QThread):
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, input_file, output_file, resolution_preset, hw_preset, start_time, end_time, filter_idx=0, add_watermark=False, mute_audio=False, manual_crop_data=None):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.resolution_preset = resolution_preset
        self.hw_preset = hw_preset
        self.start_time = start_time
        self.end_time = end_time
        self.filter_idx = filter_idx
        self.add_watermark = add_watermark
        self.mute_audio = mute_audio
        self.manual_crop_data = manual_crop_data
        self._is_running = True

    def run(self):
        preset_map = {
            0: "1080:1920", # 9:16
            1: "1920:1080", # 1080p
            2: "2560:1440", # 2K
            3: "3840:2160"  # 4K
        }
        
        # Donanım Hızlandırma Seçimi
        hw_args = []
        if self.hw_preset == 1: # NVIDIA NVENC
            hw_args = ["-c:v", "h264_nvenc", "-preset", "p6", "-b:v", "10M"]
        elif self.hw_preset == 2: # AMD AMF
            hw_args = ["-c:v", "h264_amf", "-quality", "quality", "-b:v", "10M"]
        else: # CPU
            hw_args = ["-c:v", "libx264", "-preset", "slow", "-crf", "18"]
        
        # Kesme (Trimming)
        trim_args = []
        if self.start_time is not None and self.end_time is not None:
            if self.end_time > self.start_time:
                trim_args = ["-ss", str(self.start_time), "-to", str(self.end_time)]

        # --- FİLTRE ZİNCİRİ OLUŞTURMA ---
        filters = []
        
        # 1. Kırpma veya Ölçeklendirme
        if self.resolution_preset == 4 and self.manual_crop_data:
            # Manuel Kırpma: (W, H, X, Y)
            cw, ch, cx, cy = self.manual_crop_data
            filters.append(f"crop={cw}:{ch}:{cx}:{cy}")
        else:
            # Otomatik Ölçeklendirme ve Padding
            target_res = preset_map.get(self.resolution_preset, "1920:1080")
            filters.append(f"scale={target_res}:force_original_aspect_ratio=decrease,pad={target_res}:(ow-iw)/2:(oh-ih)/2")
        
        # Format sabitleme (Renk uzayı uyumluluğu için)
        filters.append("format=yuv420p")
        
        # 2. Renk Filtreleri
        # 0: Orijinal, 1: Sinematik, 2: Canlı, 3: Siyah Beyaz, 4: Vintage, 5: Matrix, 6: Güneşli, 7: Bulanık
        if self.filter_idx == 1:
            filters.append("eq=contrast=1.3:saturation=0.8:gamma=0.9") # Sinematik
        elif self.filter_idx == 2:
            filters.append("eq=saturation=1.5:contrast=1.1") # Canlı
        elif self.filter_idx == 3:
            filters.append("hue=s=0") # Siyah Beyaz
        elif self.filter_idx == 4:
            filters.append("colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131") # Sepia/Vintage
        elif self.filter_idx == 5:
            filters.append("colorbalance=rs=-0.3:gs=0.2:bs=-0.3") # Matrix (Yeşil/Soğuk)
        elif self.filter_idx == 6:
            filters.append("colorbalance=rs=0.2:bs=-0.2") # Güneşli (Sıcak/Sarı-Kırmızı)
        elif self.filter_idx == 7:
            filters.append("boxblur=luma_radius=5:luma_power=1") # Bulanık (Dream Glow)
            
        video_filter_chain = ",".join(filters)
        
        cmd = ["ffmpeg", "-y"] + trim_args + ["-i", self.input_file]
        
        if self.add_watermark:
            # Filigran için complex_filter
            from utils import get_resource_path
            logo_path = get_resource_path(os.path.join("assets", "ripleytia_r_logo.jpg"))
            cmd += ["-i", logo_path]
            
            # [0:v] -> ana video filtresi -> [vbase]
            # [1:v] -> logoyu küçült ve şeffaflaştır (jpg olduğu için lutyuv/format ile pseudo-alpha yapabiliriz veya sabit boyutlandırırız)
            # Daha güvenli basit overlay: Sağ alta (W-w-20):(H-h-20)
            complex_filter = f"[0:v]{video_filter_chain}[bg]; [1:v]scale=80:-1[wm]; [bg][wm]overlay=W-w-20:H-h-20[outv]"
            cmd += ["-filter_complex", complex_filter, "-map", "[outv]"]
        else:
            # Normal video filtresi
            cmd += ["-vf", video_filter_chain]
            
        cmd += hw_args
        
        # Ses Ayarları
        if self.mute_audio:
            cmd.append("-an")
        else:
            if self.add_watermark:
                cmd += ["-map", "0:a?"] # Ses varsa al
            cmd += ["-c:a", "copy"]
            
        cmd.append(self.output_file)
        
        self.log_updated.emit(f"[*] FFmpeg komutu başlatılıyor:\n{' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            for line in process.stdout:
                if not self._is_running:
                    process.kill()
                    self.finished.emit(False, "İşlem iptal edildi.")
                    return
                
                if "frame=" in line or "Error" in line:
                    self.log_updated.emit(line.strip())

            process.wait()
            
            if process.returncode == 0:
                self.finished.emit(True, f"İşlem başarıyla tamamlandı: {self.output_file}")
            else:
                self.finished.emit(False, f"Hata oluştu. Çıkış kodu: {process.returncode}")
                
        except Exception as e:
            self.finished.emit(False, f"İstisna oluştu: {str(e)}")

    def stop(self):
        self._is_running = False

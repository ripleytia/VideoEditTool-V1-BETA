# Ripleytia Video Suite - Build Script

Write-Host ">>> Gereksinimler yükleniyor..." -ForegroundColor Cyan
pip install pyinstaller pillow

Write-Host ">>> İkon dosyası (.ico) oluşturuluyor..." -ForegroundColor Cyan
python -c "
from PIL import Image
import os
try:
    img = Image.open('assets/ripleytia_r_logo.jpg')
    img.save('assets/icon.ico', format='ICO', sizes=[(256, 256)])
    print('İkon başarıyla oluşturuldu.')
except Exception as e:
    print('İkon oluşturulurken hata:', e)
"

Write-Host ">>> PyInstaller ile .exe derleniyor..." -ForegroundColor Cyan
# Windows path separator for add-data is ';'
pyinstaller --noconfirm --onedir --windowed --icon "assets/icon.ico" --name "RipleytiaVideoSuite" --add-data "assets;assets/" --add-data "styles;styles/" main.py

Write-Host ">>> Derleme tamamlandı!" -ForegroundColor Green
Write-Host "Çıktı klasörü: dist\RipleytiaVideoSuite" -ForegroundColor Green
Write-Host "NOT: Kullanıcıların bilgisayarında FFmpeg'in yüklü olması veya FFmpeg binary (ffmpeg.exe) dosyalarının uygulamanın bulunduğu dizine kopyalanması gerekmektedir." -ForegroundColor Yellow

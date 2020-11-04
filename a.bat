
@echo off
set ip_address_string="IPv4 Address"
set port=1025
for /f "usebackq tokens=2 delims=:" %%f in (`ipconfig ^| findstr /c:%ip_address_string%`) do start cmd.exe /c "python ClientLauncher.py %%f %port% 5008 video.mjpeg"
python Server.py %port%


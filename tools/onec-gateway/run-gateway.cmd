@echo off
setlocal
cd /d C:\WFM1CGateway
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\WFM1CGateway\gateway.ps1 -ListenPrefix "http://+:8088/"

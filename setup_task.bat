@echo off
schtasks /create /tn "PratternDailyScan" /tr "C:\Users\prave\OneDrive\Documents\Apps\Prattern\run_scan.bat" /sc weekly /d MON,TUE,WED,THU,FRI /st 16:30 /f
pause

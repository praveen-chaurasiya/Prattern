@echo off
:: Pratten Daily Scanner — launched by Task Scheduler weekdays at 16:30 ET
cd /d "%~dp0"

if not exist logs mkdir logs

echo ============================================================ >> logs\scan_log.txt
echo Scan started: %date% %time% >> logs\scan_log.txt
echo ============================================================ >> logs\scan_log.txt

python jobs\scan_universe.py >> logs\scan_log.txt 2>&1

echo Scan finished: %date% %time% >> logs\scan_log.txt

echo ============================================================ >> logs\scan_log.txt
echo Analysis started: %date% %time% >> logs\scan_log.txt
echo ============================================================ >> logs\scan_log.txt

python jobs\analyze_movers.py >> logs\scan_log.txt 2>&1

echo Analysis finished: %date% %time% >> logs\scan_log.txt
echo. >> logs\scan_log.txt

@echo off
echo Starting PostgreSQL backup for GrowEasy_Web...

:: Run pg_dump with the external database URL
pg_dump -d postgresql://groweasy_web_user:DgIu3tONEj7gN7QAyQDPLUo1KkwPpkY8@dpg-d1rvoa6r433s73b875g0-a.oregon-postgres.render.com/groweasy_web > backup.sql

if %ERRORLEVEL% equ 0 (
    echo Backup completed successfully. File: backup.sql
) else (
    echo Error: Backup failed. Check the command or network connection.
)

pause
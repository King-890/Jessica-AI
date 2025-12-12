@echo off
echo Deploying Supabase Project...

REM Check if Supabase CLI is in PATH
call supabase --version >nul 2>&1
if %errorlevel% equ 0 (
    set SUPABASE_CMD=supabase
    goto Found
)

REM Check if installed via Scoop but not in PATH
if exist "%USERPROFILE%\scoop\shims\supabase.exe" (
    set SUPABASE_CMD="%USERPROFILE%\scoop\shims\supabase.exe"
    goto Found
)

echo Supabase CLI is not installed or not in PATH.
echo Please install it e.g. 'scoop install supabase' and restart your terminal.
exit /b 1

:Found
echo Found Supabase CLI: %SUPABASE_CMD%

REM Load .env file
if exist .env (
    echo Loading variables from .env...
    for /f "tokens=1* delims==" %%a in ('type .env') do (
        set %%a=%%b
    )
) else (
    echo Warning: .env file not found.
)

REM Link Project if PROJECT_ID is set
if defined PROJECT_ID (
    echo Linking project %PROJECT_ID%...
    call %SUPABASE_CMD% link --project-ref %PROJECT_ID% --password "%SUPABASE_DB_PASSWORD%"
) else (
    echo Warning: PROJECT_ID not found in .env. Deployment might fail if not linked.
)

REM Deploy Database Migrations
echo Deploying Migrations...
call %SUPABASE_CMD% db push

REM Deploy Edge Functions
echo Deploying Edge Functions...
call %SUPABASE_CMD% functions deploy embed-generator --project-ref %PROJECT_ID%
call %SUPABASE_CMD% functions deploy enqueue-inference --project-ref %PROJECT_ID%
call %SUPABASE_CMD% functions deploy run-inference-worker --project-ref %PROJECT_ID%
call %SUPABASE_CMD% functions deploy auth-proxy --project-ref %PROJECT_ID%

echo Deployment Complete.
pause

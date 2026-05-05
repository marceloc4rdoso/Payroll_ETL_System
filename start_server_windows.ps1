$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$env:DJANGO_ALLOW_LAN = "1"
$env:DJANGO_SETTINGS_MODULE = "core.settings"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
  throw "Python do venv não encontrado em: $Python"
}

& $Python -m pip --version | Out-Null

& $Python manage.py migrate --noinput

$Bind = $env:DJANGO_BIND
if ([string]::IsNullOrWhiteSpace($Bind)) { $Bind = "0.0.0.0:8000" }

& $Python manage.py runserver $Bind --noreload

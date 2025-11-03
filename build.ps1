# build.ps1 - Script de build para generar un único .exe con PyInstaller
# Uso: Ejecutar desde PowerShell en la raíz del proyecto
# Recomendado: Ejecutar dentro de un entorno virtual (.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
Push-Location $projectRoot

Write-Host "Proyecto: $projectRoot"

# Activar venv si existe
$venvActivate = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "Activando entorno virtual..."
    & $venvActivate
} else {
    Write-Host "No se encontró .venv. Se usará el Python del sistema o el que tengas activo."
}

# Comprobar dependencias con el script Python
Write-Host "Comprobando dependencias necesarias para build (PyInstaller, PyQt6)..."
$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Get-Command py -ErrorAction SilentlyContinue) { "py -3" } else { $null }
if (-not $py) {
    Write-Error "No se encontró 'python' en la PATH. Instala Python 3.8+ y vuelve a ejecutar."
    Exit 1
}

& $py check_build_deps.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Algunas dependencias faltan. ¿Deseas instalarlas ahora? (Y/N)"
    $ans = Read-Host
    if ($ans -match '^(Y|y)') {
        Write-Host "Instalando PyInstaller y PyQt6..."
        & $py -m pip install --upgrade pip
        & $py -m pip install pyinstaller PyQt6
    } else {
        Write-Error "Cancelado por el usuario. Instala las dependencias e intenta de nuevo."
        Exit 1
    }
}

# Opciones de build
$exeName = "empresa_app"
$entryScript = "empresa.py"

# Preparar --add-data para recursos si existen (no generamos archivos en el build)
$addDataArgs = @()
$estilo = Join-Path $projectRoot "estilo.css"
if (Test-Path $estilo) { $addDataArgs += "$estilo;." }
$image = Join-Path $projectRoot "image.jpeg"
if (Test-Path $image) { $addDataArgs += "$image;." }

# Construir la cadena de add-data para PyInstaller (PowerShell; separar entradas con espacio)
$addDataParams = @()
foreach ($a in $addDataArgs) { $addDataParams += "--add-data"; $addDataParams += $a }

# Comando PyInstaller
$pyinstallerArgs = @(
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name", $exeName,
    $entryScript
) + $addDataParams

Write-Host "Ejecutando PyInstaller..."
Write-Host "pyinstaller $($pyinstallerArgs -join ' ')"
& pyinstaller @pyinstallerArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller falló. Revisa la salida de error arriba."
    Pop-Location
    Exit 1
}

# Copiar resultado a release\
$distExe = Join-Path $projectRoot "dist\$exeName.exe"
$releaseDir = Join-Path $projectRoot "release"
if (-not (Test-Path $releaseDir)) { New-Item -ItemType Directory -Path $releaseDir | Out-Null }
Copy-Item -Path $distExe -Destination (Join-Path $releaseDir "$exeName.exe") -Force
Write-Host "Build completado. Ejecutable en: $releaseDir\$exeName.exe"
Write-Host "Si deseas una distribución portable, copia también 'empresa.db' (si la tienes) al mismo directorio que el exe."

Write-Host "Nota: No se generó ni copió 'estilo.css' durante el build. Si deseas que el exe use estilos externos, coloca 'estilo.css' junto al exe." 

Pop-Location

<#
Grant full control permissions to current user for common user folders + custom paths.

Usage:
  .\grant_permissions.ps1
  .\grant_permissions.ps1 -All
#>

param(
    [switch]$All
)

function Get-CurrentUserIdentity {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $current -or -not $current.User) {
        throw "No se pudo resolver la identidad del usuario actual."
    }

    try {
        return $current.User.Translate([Security.Principal.NTAccount]).Value
    } catch {
        return "$env:USERDOMAIN\$env:USERNAME"
    }
}

function Grant-Permissions($path) {
    if (-not (Test-Path $path)) {
        Write-Host "Path not found: $path" -ForegroundColor Yellow
        return
    }

    $identity = Get-CurrentUserIdentity

    try {
        $acl = Get-Acl -Path $path
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $identity,
            "FullControl",   # 🔹 Permisos de Control Total
            "ContainerInherit, ObjectInherit",
            "None",
            "Allow"
        )
        $acl.SetAccessRule($rule)
        Set-Acl -Path $path -AclObject $acl
        Write-Host "Permisos de CONTROL TOTAL otorgados para: $path" -ForegroundColor Green
    } catch {
        Write-Host "No se pudieron aplicar permisos a: $path" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

# Carpetas comunes + rutas adicionales
$common = @(
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Desktop')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Documents')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Downloads')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Pictures')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Music')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Videos')
    'D:\IA\Asistente'              # 🔹 Nueva ruta
    'D:\IA\Asistente\Report'       # 🔹 Nueva ruta
)

if ($All) {
    Write-Host "ADVERTENCIA: va a aplicar permisos a TODAS las carpetas de $env:USERPROFILE" -ForegroundColor Yellow
    $confirm = Read-Host "Escriba YES para confirmar"
    if ($confirm -ne 'YES') {
        Write-Host "Operación cancelada por el usuario." -ForegroundColor Cyan
        exit 1
    }

    $dirs = Get-ChildItem -Path $env:USERPROFILE -Directory -Force |
        Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } |
        ForEach-Object { $_.FullName }

    foreach ($d in $dirs) {
        if ($d -match '\\AppData$') { continue }
        Grant-Permissions -path $d
    }
} else {
    Write-Host "Aplicando permisos de CONTROL TOTAL a carpetas comunes y rutas adicionales: $($common -join ', ')" -ForegroundColor Cyan
    foreach ($p in $common) {
        Grant-Permissions -path $p
    }
}

Write-Host "Operación finalizada. Revise los resultados y ajuste manualmente si es necesario." -ForegroundColor Cyan

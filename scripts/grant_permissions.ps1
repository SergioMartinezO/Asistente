<#
Grant write/modify permissions to current user for common user folders.

Usage:
  # Apply to common visible folders (Desktop, Documents, Downloads, Pictures, Music, Videos)
  .\grant_permissions.ps1

  # Apply to all top-level folders under the user profile (DANGEROUS: will prompt for confirmation)
  .\grant_permissions.ps1 -All
#>

param(
    [switch]$All
)

function Get-CurrentUserSid {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    return $current.User.Value
}

function Grant-Permissions($path) {
    if (-not (Test-Path $path)) {
        Write-Host "Path not found: $path" -ForegroundColor Yellow
        return
    }

    $sid = Get-CurrentUserSid
    try {
        $acl = Get-Acl -Path $path
    } catch {
        Write-Host "No se pudo leer ACL para: $path" -ForegroundColor Red
        return
    }

    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid, "Modify", "ContainerInherit, ObjectInherit", "None", "Allow")
    $acl.SetAccessRule($rule)

    try {
        Set-Acl -Path $path -AclObject $acl
        Write-Host "Permisos otorgados para: $path" -ForegroundColor Green
    } catch {
        Write-Host "No se pudieron aplicar permisos a: $path" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

# Common visible user folders
$common = @(
    Join-Path $env:USERPROFILE 'Desktop',
    Join-Path $env:USERPROFILE 'Documents',
    Join-Path $env:USERPROFILE 'Downloads',
    Join-Path $env:USERPROFILE 'Pictures',
    Join-Path $env:USERPROFILE 'Music',
    Join-Path $env:USERPROFILE 'Videos'
)

if ($All) {
    Write-Host "ADVERTENCIA: va a aplicar permisos a TODAS las carpetas de $env:USERPROFILE" -ForegroundColor Yellow
    $confirm = Read-Host "Escriba YES para confirmar"
    if ($confirm -ne 'YES') {
        Write-Host "Operación cancelada por el usuario." -ForegroundColor Cyan
        exit 1
    }

    $dirs = Get-ChildItem -Path $env:USERPROFILE -Directory -Force | ForEach-Object { $_.FullName }
    foreach ($d in $dirs) {
        # opcional: saltar AppData por seguridad
        if ($d -match '\\AppData$') { continue }
        Grant-Permissions -path $d
    }
} else {
    Write-Host "Aplicando permisos a carpetas comunes: $($common -join ', ')" -ForegroundColor Cyan
    foreach ($p in $common) {
        Grant-Permissions -path $p
    }
}

Write-Host "Operación finalizada. Revise los resultados y ajuste manualmente si es necesario." -ForegroundColor Cyan

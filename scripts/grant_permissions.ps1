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

function Get-CurrentUserIdentity {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not $current -or -not $current.User) {
        throw "No se pudo resolver la identidad del usuario actual."
    }

    try {
        # Usar NTAccount evita errores de traducción con FileSystemAccessRule
        return $current.User.Translate([Security.Principal.NTAccount]).Value
    } catch {
        # Fallback por compatibilidad
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
            "Modify",
            "ContainerInherit, ObjectInherit",
            "None",
            "Allow"
        )
        $acl.SetAccessRule($rule)
        Set-Acl -Path $path -AclObject $acl
        Write-Host "Permisos otorgados para: $path" -ForegroundColor Green
    } catch {
        Write-Host "No se pudieron aplicar permisos a: $path" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

# Common visible user folders
$common = @(
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Desktop')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Documents')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Downloads')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Pictures')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Music')
    (Join-Path -Path $env:USERPROFILE -ChildPath 'Videos')
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

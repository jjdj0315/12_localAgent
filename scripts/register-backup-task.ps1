<#
.SYNOPSIS
    Windows 작업 스케줄러에 백업 작업 등록

.DESCRIPTION
    일일 백업 스크립트를 Windows 작업 스케줄러에 등록하여 매일 새벽 2시 자동 실행

.PARAMETER ScriptPath
    백업 스크립트 경로 (기본값: 현재 디렉토리의 backup-daily.ps1)

.EXAMPLE
    .\register-backup-task.ps1
    .\register-backup-task.ps1 -ScriptPath "C:\app\scripts\backup-daily.ps1"

.NOTES
    요구사항:
    - 관리자 권한 필요
    - backup-daily.ps1 스크립트 존재
#>

param(
    [string]$ScriptPath = (Join-Path $PSScriptRoot "backup-daily.ps1")
)

# 관리자 권한 확인
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "이 스크립트는 관리자 권한이 필요합니다. PowerShell을 관리자로 실행해주세요."
    exit 1
}

# 스크립트 존재 확인
if (-not (Test-Path $ScriptPath)) {
    Write-Error "백업 스크립트를 찾을 수 없습니다: $ScriptPath"
    exit 1
}

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "백업 작업 스케줄러 등록" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

try {
    # 기존 작업 삭제 (있는 경우)
    $taskName = "LLM-WebApp-DailyBackup"
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "`n기존 작업 제거 중..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }

    # 작업 동작 정의
    $action = New-ScheduledTaskAction `
        -Execute "PowerShell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

    # 트리거 정의 (매일 02:00)
    $trigger = New-ScheduledTaskTrigger -Daily -At 2am

    # 주체 정의 (SYSTEM 계정으로 실행)
    $principal = New-ScheduledTaskPrincipal `
        -UserId "SYSTEM" `
        -LogonType ServiceAccount `
        -RunLevel Highest

    # 설정 정의
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable

    # 작업 등록
    Write-Host "`n작업 등록 중..." -ForegroundColor Yellow
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Local LLM 웹앱 일일 백업 (매일 새벽 2시)" | Out-Null

    Write-Host "`n=====================================" -ForegroundColor Cyan
    Write-Host "✓ 백업 작업 등록 완료!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host "`n작업 정보:" -ForegroundColor White
    Write-Host "  - 작업 이름: $taskName" -ForegroundColor Gray
    Write-Host "  - 실행 시각: 매일 02:00" -ForegroundColor Gray
    Write-Host "  - 스크립트: $ScriptPath" -ForegroundColor Gray
    Write-Host "  - 실행 계정: SYSTEM" -ForegroundColor Gray

    # 작업 상태 확인
    Write-Host "`n등록된 작업 확인:" -ForegroundColor White
    $task = Get-ScheduledTask -TaskName $taskName
    Write-Host "  - 상태: $($task.State)" -ForegroundColor Gray
    Write-Host "  - 다음 실행 시각: $((Get-ScheduledTaskInfo -TaskName $taskName).NextRunTime)" -ForegroundColor Gray

    Write-Host "`n작업 스케줄러에서 확인하려면:" -ForegroundColor Yellow
    Write-Host "  taskschd.msc" -ForegroundColor White

} catch {
    Write-Host "`n❌ 작업 등록 실패: $_" -ForegroundColor Red
    exit 1
}

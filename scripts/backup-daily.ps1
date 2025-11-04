<#
.SYNOPSIS
    일일 증분 백업 스크립트 (Windows용)

.DESCRIPTION
    PostgreSQL 데이터베이스와 업로드된 문서를 증분 백업합니다.
    매일 새벽 2시 실행 (Windows 작업 스케줄러 등록)

.NOTES
    요구사항:
    - PostgreSQL 클라이언트 도구 (pg_dump)
    - Robocopy (Windows 기본 제공)

    환경변수:
    - POSTGRES_PASSWORD: PostgreSQL 암호
#>

$ErrorActionPreference = "Stop"

# 설정
$BACKUP_DIR = "D:\backups\daily"  # 백업 저장 경로
$DB_NAME = "llm_webapp"
$DB_USER = "postgres"
$DB_HOST = "localhost"
$PGPASSWORD = $env:POSTGRES_PASSWORD  # 환경변수에서 읽기
$UPLOAD_DIR = "C:\app\uploads"

$timestamp = Get-Date -Format "yyyyMMdd"
$logFile = "$BACKUP_DIR\backup_$timestamp.log"

function Write-Log {
    param([string]$Message)
    $logMessage = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

try {
    Write-Log "일일 백업 시작"

    # 백업 디렉토리 생성
    if (-not (Test-Path $BACKUP_DIR)) {
        New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    }

    # 1. PostgreSQL 백업
    Write-Log "PostgreSQL 백업 시작: $DB_NAME"
    $dbBackupFile = "$BACKUP_DIR\db_$timestamp.dump"

    $env:PGPASSWORD = $PGPASSWORD
    & pg_dump -h $DB_HOST -U $DB_USER -F c -d $DB_NAME -f $dbBackupFile

    if ($LASTEXITCODE -eq 0) {
        $dbSize = [math]::Round((Get-Item $dbBackupFile).Length / 1MB, 2)
        Write-Log "✓ DB 백업 완료: $dbBackupFile ($dbSize MB)"
    } else {
        throw "PostgreSQL 백업 실패 (종료 코드: $LASTEXITCODE)"
    }

    # 2. 문서 파일 백업 (증분 - Robocopy 미러링)
    Write-Log "문서 파일 백업 시작: $UPLOAD_DIR"
    $docsBackupDir = "$BACKUP_DIR\uploads_$timestamp"

    # Robocopy: /MIR (미러링), /R:3 (재시도 3회), /W:10 (대기 10초), /LOG+ (로그 추가)
    robocopy $UPLOAD_DIR $docsBackupDir /MIR /R:3 /W:10 /LOG+:$logFile /NP /NDL /NFL

    # Robocopy 종료 코드: 0-7 정상, 8+ 에러
    if ($LASTEXITCODE -le 7) {
        $docsSize = [math]::Round((Get-ChildItem $docsBackupDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
        Write-Log "✓ 문서 백업 완료: $docsBackupDir ($docsSize MB)"
    } else {
        throw "문서 파일 백업 실패 (Robocopy 오류 코드: $LASTEXITCODE)"
    }

    Write-Log "======================================"
    Write-Log "✓ 일일 백업 성공 완료"
    Write-Log "======================================"

} catch {
    Write-Log "❌ 백업 실패: $_"

    # 관리자에게 이메일 알림 (선택 사항 - SMTP 설정 필요)
    # Send-MailMessage -To "admin@example.com" -Subject "백업 실패 알림" -Body $_ -SmtpServer "smtp.example.com"

    exit 1
}

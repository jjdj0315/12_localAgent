<#
.SYNOPSIS
    오프라인 배포용 의존성 번들 생성 스크립트 (Windows용)

.DESCRIPTION
    폐쇄망 환경 배포를 위해 Python 패키지, AI 모델, 설정 파일을 로컬에 다운로드하여 tarball로 패키징합니다.
    Constitution Principle VI (Windows 개발 환경 호환성) 준수

.PARAMETER OutputDir
    번들 파일 출력 디렉토리 (기본값: ./offline_bundle)

.EXAMPLE
    .\bundle-offline-deps.ps1
    .\bundle-offline-deps.ps1 -OutputDir "C:\temp\bundle"

.NOTES
    실행 전 요구사항:
    - Python 3.11+ 설치됨
    - pip install huggingface-hub (huggingface-cli 사용)
    - 인터넷 연결 필요 (다운로드)
#>

param(
    [string]$OutputDir = ".\offline_bundle"
)

# 에러 발생 시 중단
$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "오프라인 의존성 번들 생성 시작" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# 1. 출력 디렉토리 생성
Write-Host "`n[1/6] 출력 디렉토리 생성: $OutputDir" -ForegroundColor Yellow
if (Test-Path $OutputDir) {
    Remove-Item -Path $OutputDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputDir\python_packages" -Force | Out-Null
New-Item -ItemType Directory -Path "$OutputDir\models" -Force | Out-Null

# 2. Python 패키지 다운로드
Write-Host "`n[2/6] Python 패키지 다운로드 (requirements.txt)" -ForegroundColor Yellow
$requirementsPath = Join-Path $PSScriptRoot "..\backend\requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    Write-Error "requirements.txt를 찾을 수 없습니다: $requirementsPath"
    exit 1
}

pip download -d "$OutputDir\python_packages" -r $requirementsPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python 패키지 다운로드 실패"
    exit 1
}
Write-Host "✓ Python 패키지 다운로드 완료" -ForegroundColor Green

# 3. AI 모델 다운로드
Write-Host "`n[3/6] AI 모델 다운로드" -ForegroundColor Yellow

# 3.1 LLM 모델 (Qwen3-4B-Instruct GGUF)
Write-Host "  - Qwen3-4B-Instruct GGUF 다운로드 중..." -ForegroundColor Gray
huggingface-cli download Qwen/Qwen3-4B-Instruct-GGUF `
    qwen3-4b-instruct-q4_k_m.gguf `
    --local-dir "$OutputDir\models\qwen3-4b-gguf" `
    --local-dir-use-symlinks False
if ($LASTEXITCODE -ne 0) {
    Write-Error "Qwen3-4B GGUF 다운로드 실패"
    exit 1
}

# 3.2 Safety Filter 모델 (toxic-bert)
Write-Host "  - unitary/toxic-bert 다운로드 중..." -ForegroundColor Gray
huggingface-cli download unitary/toxic-bert `
    --local-dir "$OutputDir\models\toxic-bert" `
    --local-dir-use-symlinks False

# 3.3 Embedding 모델 (sentence-transformers)
Write-Host "  - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 다운로드 중..." -ForegroundColor Gray
huggingface-cli download sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 `
    --local-dir "$OutputDir\models\embeddings" `
    --local-dir-use-symlinks False

Write-Host "✓ 모든 AI 모델 다운로드 완료" -ForegroundColor Green

# 4. 설정 파일 복사
Write-Host "`n[4/6] 설정 파일 복사" -ForegroundColor Yellow
$dataPath = Join-Path $PSScriptRoot "..\backend\data\korean_holidays.json"
$templatesPath = Join-Path $PSScriptRoot "..\backend\templates"

if (Test-Path $dataPath) {
    Copy-Item -Path $dataPath -Destination "$OutputDir\korean_holidays.json"
}
if (Test-Path $templatesPath) {
    Copy-Item -Path $templatesPath -Destination "$OutputDir\templates" -Recurse
}
Write-Host "✓ 설정 파일 복사 완료" -ForegroundColor Green

# 5. Manifest 생성
Write-Host "`n[5/6] Manifest 파일 생성" -ForegroundColor Yellow
$totalSize = [math]::Round((Get-ChildItem $OutputDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB, 2)
$packageCount = (Get-ChildItem "$OutputDir\python_packages" | Measure-Object).Count

$manifest = @"
# 오프라인 배포 번들 Manifest
생성 일시: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
생성자: $env:USERNAME

## 포함 내용

### Python 패키지 ($packageCount개 파일)
- 위치: python_packages/
- 설치: pip install --no-index --find-links=python_packages/ -r requirements.txt

### AI 모델
1. Qwen3-4B-Instruct GGUF (~2.5GB)
   - 위치: models/qwen3-4b-gguf/
   - 배포 경로: /models/qwen3-4b-instruct-q4_k_m.gguf

2. toxic-bert (~400MB)
   - 위치: models/toxic-bert/
   - 배포 경로: /backend/app/models_storage/toxic-bert/

3. sentence-transformers (~420MB)
   - 위치: models/embeddings/
   - 배포 경로: /models/embeddings/

### 설정 파일
- korean_holidays.json → backend/data/
- templates/ → backend/templates/

## 번들 크기
총 용량: $totalSize GB

## 검증 체크리스트
- [ ] Python 패키지 설치 성공
- [ ] Qwen3-4B GGUF 로드 성공
- [ ] toxic-bert 로드 성공
- [ ] sentence-transformers 로드 성공
- [ ] korean_holidays.json 접근 가능
- [ ] templates 디렉토리 접근 가능
"@

$manifest | Out-File -FilePath "$OutputDir\MANIFEST.md" -Encoding UTF8

# 6. 압축 (ZIP 형식, Windows 호환)
Write-Host "`n[6/6] 번들 압축 중..." -ForegroundColor Yellow
$zipFile = ".\offline_bundle_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
Compress-Archive -Path "$OutputDir\*" -DestinationPath $zipFile -Force
$zipSize = [math]::Round((Get-Item $zipFile).Length / 1GB, 2)

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "✓ 번들 생성 완료!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "파일: $zipFile ($zipSize GB)" -ForegroundColor White
Write-Host "Manifest: $OutputDir\MANIFEST.md" -ForegroundColor White
Write-Host "`n폐쇄망 서버로 전송 후 압축 해제하여 사용하세요." -ForegroundColor Yellow

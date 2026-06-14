Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Local Small Model Launcher (Windows) ==="

# Config
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ModelRepo   = "Qwen/Qwen2.5-1.5B-Instruct"
$ModelDir    = Join-Path $ProjectRoot "models\small\qwen25-1.5b-instruct"
$VenvDir     = Join-Path $ProjectRoot ".venv-small"
$LogDir      = Join-Path $ProjectRoot "logs"
$Port        = 8000
$ApiBase     = "http://127.0.0.1:$Port"
$LogFile     = Join-Path $LogDir "small_model_server.log"

# Ensure dirs
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir  | Out-Null

# 1) Python check
try {
    $pyVer = python --version 2>&1
    Write-Host "Python: $pyVer"
} catch {
    throw "Python not found in PATH. Install Python 3.10+ first."
}

# 2) Create venv if missing
if (-not (Test-Path (Join-Path $VenvDir "Scripts\python.exe"))) {
    Write-Host "Creating venv: $VenvDir"
    python -m venv $VenvDir
}

# Activate venv
$activate = Join-Path $VenvDir "Scripts\Activate.ps1"
. $activate

# 3) Install dependencies
Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
pip install huggingface_hub llama-cpp-python

# 4) Download model (use mirror in China)
$env:HF_ENDPOINT = "https://hf-mirror.com"
$modelFile = Join-Path $ModelDir "model.gguf"
if (-not (Test-Path $modelFile)) {
    Write-Host "Downloading model: $ModelRepo -> $ModelDir"
    huggingface-cli download $ModelRepo --local-dir $ModelDir
} else {
    Write-Host "Model already exists: $modelFile"
}

# 5) Start OpenAI-compatible server
Write-Host "Starting llama-cpp-python server on port $Port ..."
$serverCmd = "from llama_cpp.server.app import create_app; import uvicorn; app=create_app(model='$ModelDir', n_ctx=2048); uvicorn.run(app, host='127.0.0.1', port=$Port)"
Start-Process -FilePath (Join-Path $VenvDir "Scripts\python.exe") -ArgumentList "-c `"$serverCmd`"" -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile -WindowStyle Hidden

# 6) Wait for health
Write-Host "Waiting for API at $ApiBase ..."
for ($i=0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "$ApiBase/v1/models"
        if ($r.StatusCode -eq 200) { break }
    } catch {}
    Start-Sleep -Seconds 2
}

# 7) Test request
Write-Host "Sending test request..."
$testPrompt = "分析投诉文本，归类标签并提取诉求。\n衣服线头全开了，退钱！"
$body = @{
    model = "qwen25-1.5b-instruct"
    messages = @(@{ role="user"; content=$testPrompt })
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri "$ApiBase/v1/chat/completions" -Body $body -ContentType "application/json"

Write-Host "Done. API running at $ApiBase"
Write-Host "Logs: $LogFile"

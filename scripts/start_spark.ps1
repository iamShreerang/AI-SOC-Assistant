# Start Real Spark Streaming Job on Windows
# Configures JDK 17, HADOOP_HOME (winutils), and starts streaming_job.py

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ToolsDir = Join-Path $RepoRoot "tools"
$JdkDir = Join-Path $ToolsDir "jdk-17.0.10+7"
$HadoopDir = Join-Path $ToolsDir "hadoop"
$HadoopBin = Join-Path $HadoopDir "bin"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " AI SOC Assistant — Windows Real Spark Streaming Launcher   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Verify & Configure JAVA_HOME
if (Test-Path $JdkDir) {
    $env:JAVA_HOME = $JdkDir
    $env:PATH = "$JdkDir\bin;" + $env:PATH
    Write-Host "[OK] Using project JDK 17: $JdkDir" -ForegroundColor Green
} else {
    Write-Host "[INFO] Using system JAVA_HOME: $env:JAVA_HOME" -ForegroundColor Yellow
}

# Verify & Configure HADOOP_HOME
if (Test-Path $HadoopBin) {
    $env:HADOOP_HOME = $HadoopDir
    $env:PATH = "$HadoopBin;" + $env:PATH
    Write-Host "[OK] Using project Hadoop winutils: $HadoopBin" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Hadoop winutils not found at $HadoopBin" -ForegroundColor Red
}

Write-Host "Starting Real PySpark Structured Streaming Job (Kafka -> Spark -> FastAPI)..." -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

# Execute Spark Streaming Job
Set-Location $RepoRoot
python streaming/spark/streaming_job.py

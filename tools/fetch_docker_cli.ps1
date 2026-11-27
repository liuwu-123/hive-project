# ============================================================
#  下载 docker CLI 静态二进制到 app/bin/docker
#
#  为什么需要：
#    app 容器里的 Streamlit 要调用 `docker exec beeline` 查 Hive，
#    但 Debian 的 docker.io 包只含守护进程、不含 CLI，
#    且官方 apt 源在部分网络环境下连不上。
#    因此改用静态二进制（约 38 MB，不入 Git）。
#
#  用法：
#    .\tools\fetch_docker_cli.ps1
# ============================================================
$ErrorActionPreference = 'Stop'

$mirrors = @(
    'https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/static/stable/x86_64/docker-27.3.1.tgz',
    'https://mirrors.aliyun.com/docker-ce/linux/static/stable/x86_64/docker-27.3.1.tgz'
)
$dest  = Join-Path $PSScriptRoot '..\app\bin'
$tgz   = Join-Path $env:TEMP 'docker-static.tgz'
$ext   = Join-Path $env:TEMP 'docker-static-ext'

New-Item -ItemType Directory -Force $dest | Out-Null
if (Test-Path (Join-Path $dest 'docker')) {
    Write-Host "已存在 app\bin\docker，跳过下载" -ForegroundColor Green
    exit 0
}

$ok = $false
foreach ($u in $mirrors) {
    try {
        Write-Host "下载 $u ..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $u -OutFile $tgz -TimeoutSec 180 -UseBasicParsing
        $ok = $true
        break
    } catch {
        Write-Host "  失败: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
if (-not $ok) {
    Write-Host "所有镜像均下载失败，请手动下载 docker-27.3.1.tgz 并解压出 docker 放到 app\bin\" -ForegroundColor Red
    exit 1
}

Remove-Item $ext -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $ext | Out-Null
tar -xzf $tgz -C $ext
Copy-Item (Join-Path $ext 'docker\docker') (Join-Path $dest 'docker') -Force
Remove-Item $tgz -Force -ErrorAction SilentlyContinue

$size = (Get-Item (Join-Path $dest 'docker')).Length / 1MB
Write-Host ("已就绪：app\bin\docker（{0:N1} MB）" -f $size) -ForegroundColor Green

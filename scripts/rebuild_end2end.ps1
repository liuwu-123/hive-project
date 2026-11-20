# ============================================================
#  第 5 周：端到端一键重建（原始 CSV → ODS → DWD → DWS → ADS → MySQL 集市）
#
#  用法：
#     .\rebuild_end2end.ps1              # 全量重建（约 10~15 分钟）
#     .\rebuild_end2end.ps1 -VerifyOnly  # 不重建，只核对各层行数
#     .\rebuild_end2end.ps1 -SkipMysql   # 跳过 MySQL 集市同步
#
#  说明：
#     - 会 DROP 并重建 ydsh_ods / ydsh_dwd / ydsh_dws / ydsh_ads 四个库
#     - MySQL 侧只重建 ydsh_ads 库，不动 superset 元数据库
# ============================================================
param(
    [switch]$VerifyOnly,
    [switch]$SkipMysql
)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectDir = 'E:\hive-project'
$DataDir    = 'E:\界面\模拟数据'
$Container  = 'hive-project-hive-server-1'
$Jdbc       = 'jdbc:hive2://localhost:10000/'
$VenvPy     = Join-Path $ProjectDir '.venv\Scripts\python.exe'

function Title($t) {
    Write-Host ''
    Write-Host ('=' * 52) -ForegroundColor DarkCyan
    Write-Host "  $t" -ForegroundColor Cyan
    Write-Host ('=' * 52) -ForegroundColor DarkCyan
}
function Say($m, $c = 'Gray') { Write-Host "  $m" -ForegroundColor $c }
function OK($m)   { Write-Host "  [OK] $m" -ForegroundColor Green }
function Bad($m)  { Write-Host "  [X]  $m" -ForegroundColor Red }

function Beeline([string]$sql) {
    & docker exec $Container beeline --silent=true --showHeader=false --outputformat=csv2 -u $Jdbc -e $sql 2>$null
}

function RunSql([string]$file) {
    Say "执行 $file" 'DarkGray'
    $out = & docker exec $Container beeline --silent=true -u $Jdbc -f $file 2>&1
    $err = $out | Where-Object { $_ -match '^Error:|FAILED:' }
    if ($err) {
        Bad "$file 失败"
        $err | Select-Object -First 3 | ForEach-Object { Write-Host "      $_" -ForegroundColor Red }
        return $false
    }
    return $true
}

function Get-Num($lines) {
    # beeline 输出可能多行（含空行/告警残留），取第一个纯数字
    foreach ($l in $lines) {
        foreach ($part in ("$l" -split "`n")) {
            $v = $part.Trim().Trim('"').Replace(',', '')
            if ($v -match '^\d+$') { return [int]$v }
        }
    }
    return -1
}

function Count($table) {
    $out = Beeline "select count(*) from $table"
    return (Get-Num $out)
}

# ---------------- 1. 环境 ----------------
Title '1/8 检查环境'
$ok = $false
try { docker info 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true } } catch {}
if (-not $ok) {
    Say 'Docker Desktop 未运行，尝试启动 ...' 'Yellow'
    $exe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    if (Test-Path $exe) { Start-Process $exe | Out-Null }
    for ($i = 1; $i -le 40; $i++) {
        Start-Sleep 3
        if ($i % 5 -eq 0) { Write-Host "  等待 Docker ... $i/40" -ForegroundColor DarkGray }
        try { docker info 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { $ok = $true; break } } catch {}
    }
}
if (-not $ok) { Bad 'Docker 未就绪，退出'; exit 1 }
OK 'Docker 正常'

Push-Location $ProjectDir
docker compose up -d 2>&1 | Out-Null
Pop-Location

$ready = $false
for ($i = 1; $i -le 30; $i++) {
    $r = Beeline 'select 1'
    if ((Get-Num $r) -eq 1) { $ready = $true; break }
    if ($i % 5 -eq 0) { Write-Host "  等待 HiveServer2 ... $i/30" -ForegroundColor DarkGray }
    Start-Sleep 3
}
if (-not $ready) { Bad 'HiveServer2 未就绪，退出'; exit 1 }
OK 'HiveServer2 就绪'

if ($VerifyOnly) {
    Title '核对模式：跳过重建'
} else {
    # ---------------- 2. 清理 ----------------
    Title '2/8 清理四个库'
    foreach ($db in 'ydsh_ads', 'ydsh_dws', 'ydsh_dwd', 'ydsh_ods') {
        Beeline "drop database if exists $db cascade" | Out-Null
        Say "已删除 $db" 'DarkGray'
    }
    OK '清理完成'

    # ---------------- 3. 拷贝数据与脚本 ----------------
    Title '3/8 拷贝数据与脚本到容器'
    if (-not (Test-Path $DataDir)) { Bad "数据目录不存在：$DataDir"; exit 1 }
    docker exec -u root $Container sh -c 'mkdir -p /data /sql' | Out-Null
    docker cp "$DataDir\." "${Container}:/data/"     | Out-Null
    docker cp "$ProjectDir\sql\." "${Container}:/sql/" | Out-Null
    OK '已拷贝 6 个 CSV 与全部 SQL 脚本'

    # ---------------- 4. ODS ----------------
    Title '4/8 ODS 层：建表 + 导入'
    RunSql '/sql/ods/create_ods.sql' | Out-Null
    RunSql '/sql/ods/load_ods.sql'   | Out-Null
    OK 'ODS 完成'

    # ---------------- 5. DWD ----------------
    Title '5/8 DWD 层：清洗 + 维度 + 事实'
    foreach ($f in '/sql/clean/01_clean_user.sql', '/sql/clean/02_clean_product.sql',
                   '/sql/clean/03_dedup_order.sql',
                   '/sql/clean/10_dim_enum.sql', '/sql/clean/11_dim_user.sql',
                   '/sql/clean/12_dim_product.sql', '/sql/clean/13_dim_store_date.sql',
                   '/sql/dwd/14_fact_order.sql', '/sql/dwd/15_fact_item_behavior.sql') {
        RunSql $f | Out-Null
    }
    OK 'DWD 完成'

    # ---------------- 6. DWS / ADS ----------------
    Title '6/8 DWS + ADS 层'
    RunSql '/sql/dws/01_dws_sales.sql' | Out-Null
    RunSql '/sql/ads/02_ads_kpi.sql'   | Out-Null
    OK 'DWS / ADS 完成'

    # ---------------- 7. MySQL 集市 ----------------
    if (-not $SkipMysql) {
        Title '7/8 MySQL BI 集市'
        if (-not (Test-Path $VenvPy)) {
            Bad '未找到 .venv，跳过 MySQL 同步'
        } else {
            & $VenvPy "$ProjectDir\sync\sync_ads_to_mysql.py" 2>&1 | Select-Object -Last 3
            $sqlFile = "$ProjectDir\sql\mysql\init_ydsh_ads.sql"
            if (Test-Path $sqlFile) {
                cmd /c "docker exec -i hive-project-mysql-1 mysql -uroot -proot --default-character-set=utf8mb4 < `"$sqlFile`"" 2>$null | Out-Null
                OK 'MySQL 集市已重建'
            }
        }
    } else {
        Title '7/8 跳过 MySQL 集市'
    }
}

# ---------------- 8. 校验 ----------------
Title '8/8 各层行数核对'

$expect = [ordered]@{
    'ydsh_ods.ods_user'              = 1000
    'ydsh_ods.ods_product'           = 600
    'ydsh_ods.ods_store'             = 60
    'ydsh_ods.ods_order'             = 15600
    'ydsh_ods.ods_order_item'        = 37549
    'ydsh_ods.ods_user_behavior'     = 60000
    'ydsh_dwd.dim_user'              = 1000
    'ydsh_dwd.dim_product'           = 600
    'ydsh_dwd.dim_store'             = 60
    'ydsh_dwd.dim_date'              = 1096
    'ydsh_dwd.fact_order'            = 15000
    'ydsh_dwd.fact_order_item'       = 37549
    'ydsh_dwd.fact_behavior'         = 60000
    'ydsh_dws.dws_sales_day'         = 366
    'ydsh_dws.dws_sales_month'       = 12
    'ydsh_dws.dws_store_month'       = 720
    'ydsh_dws.dws_channel_month'     = 48
    'ydsh_dws.dws_category_month'    = 96
    'ydsh_ads.ads_kpi_overview'      = 6
    'ydsh_ads.ads_sales_daily'       = 366
    'ydsh_ads.ads_category_topn'     = 8
    'ydsh_ads.ads_store_topn'        = 60
    'ydsh_ads.ads_user_value'        = 1000
}
$fail = 0
foreach ($t in $expect.Keys) {
    $c = Count $t
    $e = $expect[$t]
    if ($c -eq $e) {
        Write-Host ("  {0,-32} {1,7}  OK" -f $t, $c) -ForegroundColor Green
    } else {
        Write-Host ("  {0,-32} {1,7}  期望 {2}" -f $t, $c, $e) -ForegroundColor Red
        $fail++
    }
}

Write-Host ''
$kpi = Beeline "select kpi_name, kpi_value, kpi_unit from ydsh_ads.ads_kpi_overview order by case kpi_name when 'GMV' then 1 when '订单量' then 2 when '客单价 AOV' then 3 when '活跃用户数' then 4 when '复购用户数' then 5 else 9 end"
($kpi -split "`n") | Where-Object { $_ -match '\|' -and $_ -notmatch 'kpi_name|---' } | ForEach-Object {
    $p = $_ -split '\|' | Where-Object { $_.Trim() -ne '' }
    if ($p.Count -ge 3) { Write-Host ("  {0,-12} {1,16} {2}" -f $p[0].Trim(), $p[1].Trim(), $p[2].Trim()) -ForegroundColor Cyan }
}

Write-Host ''
if ($fail -eq 0) {
    Write-Host '  全部核对通过，系统端到端可用。' -ForegroundColor Green
} else {
    Write-Host "  有 $fail 张表行数不符，请检查上方红字。" -ForegroundColor Red
}

param([string]$CC = 'clang', [string[]]$CompilerOptions = @(), [switch]$RunCpuTests)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Run-CC([string[]]$Arguments) {
    & $CC @CompilerOptions @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Kompajliranje nije uspjelo ($LASTEXITCODE)." }
}
$flags = @('-std=gnu11','-O2','-Wall','-Wextra','-Werror')
Run-CC ($flags + @('src/asm.c','-o','asm.exe'))
Run-CC ($flags + @('src/vm.c','src/main.c','-o','sveu16.exe','-lgdi32','-luser32'))
Run-CC ($flags + @('src/vm.c','tests/test_vm.c','-o','tests/test_vm.exe'))
& ./asm.exe firmware/boot.asm boot.rom boot.map
if ($LASTEXITCODE -ne 0) { throw 'Boot asembler: greska.' }
& ./asm.exe firmware/forth.asm forth.bin forth.map
if ($LASTEXITCODE -ne 0) { throw 'Forth asembler: greska.' }
if ((Get-Item boot.rom).Length -ne 2048) { throw 'ROM mora imati 1024 rijeci.' }
$kernel = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'forth.bin'))
if ($kernel.Length -gt 32768) { throw 'Kernel ne staje u boot podrucje.' }
# Preserve the existing working disk. The factory image is always reproducible.
$disk = New-Object byte[] 1048576
[Array]::Copy($kernel, $disk, $kernel.Length)
[IO.File]::WriteAllBytes((Join-Path $PSScriptRoot 'disk.factory.img'), $disk)
if (!(Test-Path disk.img)) { Copy-Item -LiteralPath disk.factory.img -Destination disk.img }
if ($RunCpuTests) {
    & ./tests/test_vm.exe
    if ($LASTEXITCODE -ne 0) { throw 'VM testovi nisu prosli.' }
}
Write-Host 'Izgradnja uspjesna. Pokrenite TESTIRAJ.bat, zatim POKRENI.bat.'

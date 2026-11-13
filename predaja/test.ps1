$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$output = & ./sveu16.exe '--batch' 'tests/smoke.fth' 2>&1
if ($LASTEXITCODE -ne 0) { throw "Emulator: $output" }
$text = $output -join "`n"
if ($text.Contains('?(-')) { throw "Forth greska: $text" }
foreach ($expected in @('2 3 + . 5 ', '9 KVADRAT . 81 ', '1 8 LSHIFT . 256 ', '256 4 RSHIFT . 16 ', 'SUMA . 45 ')) {
    if (!$text.Contains($expected)) { throw "Nedostaje ocekivani rezultat: $expected" }
}
$output
Write-Host 'PASS: boot, tastatura, Forth, nove rijeci, varijable, petlja i video.'

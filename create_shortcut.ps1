$Shell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path $DesktopPath "VOICEPEAK_Transmitter.lnk"

$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "D:\development\text_to_voicepeak\.venv\Scripts\pythonw.exe"
$Shortcut.Arguments = "D:\development\text_to_voicepeak\app.py"
$Shortcut.WorkingDirectory = "D:\development\text_to_voicepeak"
$Shortcut.Description = "VOICEPEAK to Discord Transmitter"
$Shortcut.Save()

Write-Host "Shortcut created on Desktop: $ShortcutPath"

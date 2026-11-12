' Compatibility launcher retained for existing Windows shortcuts.
' The actual MARGA launcher owns the persistent state and plugin environment.
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
ps = root & "\start-marga.ps1"
Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & ps & """ -Open", 0, False

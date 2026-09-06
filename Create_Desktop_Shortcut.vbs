Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
strDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strDesktop = WshShell.SpecialFolders("Desktop")
set oShellLink = WshShell.CreateShortcut(strDesktop & "\JARVIS AI.lnk")
oShellLink.TargetPath = strDir & "\Launch_Jarvis.vbs"
oShellLink.WorkingDirectory = strDir
oShellLink.WindowStyle = 0
oShellLink.Description = "JARVIS Autonomous Voice Assistant"
oShellLink.IconLocation = "shell32.dll,138"
oShellLink.Save
WScript.Echo "Desktop shortcut 'JARVIS AI' created successfully on your Desktop!"

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
strDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strDir
' Run completely silently without any command prompt or terminal window
WshShell.Run """" & strDir & "\.venv\Scripts\pythonw.exe"" """ & strDir & "\background_service.py""", 0, False


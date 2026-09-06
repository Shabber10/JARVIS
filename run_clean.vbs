Set WshShell = CreateObject("WScript.Shell")
strDir = "C:\Users\SHABBER HUSSAIN\Desktop\Jarvis"
WshShell.CurrentDirectory = strDir
WshShell.Run """" & strDir & "\.venv\Scripts\pythonw.exe"" """ & strDir & "\clean_project.py""", 0, True
Set fso = CreateObject("Scripting.FileSystemObject")
fso.DeleteFile WScript.ScriptFullName

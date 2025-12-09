
Set WshShell = CreateObject("WScript.Shell")
' Launch the continuous learning script in background (hidden window)
' Uses pythonw.exe to avoid console window
' Adjust path if python is not in PATH
WshShell.Run "pythonw src/backend/continuous_learning.py", 0, False

import os
import sys
import subprocess
import json
from pathlib import Path

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

def get_windows_notifications() -> str:
    """
    Queries active Windows 10/11 Toast Notifications (WhatsApp, System, Mail, etc.)
    and formats them for JARVIS to read out loud.
    """
    ps_command = """
[Windows.UI.Notifications.Management.UserNotificationListener, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$listener = [Windows.UI.Notifications.Management.UserNotificationListener]::Current
$access = $listener.RequestAccessAsync().GetAwaiter().GetResult()

if ($access.ToString() -ne "Allowed") {
    Write-Output "ACCESS_DENIED"
    exit
}

$notifs = $listener.GetNotificationsAsync([Windows.UI.Notifications.NotificationKinds]::Toast).GetAwaiter().GetResult()
if (-not $notifs -or $notifs.Count -eq 0) {
    Write-Output "NO_NOTIFICATIONS"
    exit
}

$items = @()
foreach ($n in $notifs) {
    $app = $n.AppInfo.DisplayInfo.DisplayName
    $binding = $n.Notification.Visual.GetBinding([Windows.UI.Notifications.KnownNotificationBindings]::ToastGeneric)
    if ($binding) {
        $texts = @()
        foreach ($t in $binding.GetTextElements()) {
            if ($t.Text -and $t.Text.Trim()) {
                $texts += $t.Text.Trim()
            }
        }
        if ($texts.Count -gt 0) {
            $msg = $texts -join " - "
            $items += "From $app: $msg"
        }
    }
}

if ($items.Count -eq 0) {
    Write-Output "NO_NOTIFICATIONS"
} else {
    $items -join "`n"
}
"""
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=CREATE_NO_WINDOW
        )
        output = res.stdout.strip()
        
        if "NO_NOTIFICATIONS" in output or not output:
            return "You have no unread notifications at the moment, Sir."
        elif "ACCESS_DENIED" in output:
            return "Windows notification access has not been granted in Windows Settings, Sir. You can enable Notification permissions under Privacy settings."
        else:
            lines = [l for l in output.splitlines() if l.strip() and not l.startswith("From :")]
            if not lines:
                return "You have no unread notifications at the moment, Sir."
            count = len(lines)
            summary = f"You have {count} recent notification{'s' if count > 1 else ''}, Sir. " + ". ".join(lines[:4])
            return summary
    except Exception as e:
        return f"Could not retrieve notifications, Sir. Subsystem notice: {e}"

if __name__ == "__main__":
    print(get_windows_notifications())

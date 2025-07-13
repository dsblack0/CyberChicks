# SnapAlert Shortcut Generator
# This script creates Windows shortcuts for custom alerts defined in data/custom_alerts.json

$python = (Get-Command python).Source
$scriptRoot = (Get-Location).Path
$launcher = "$scriptRoot\alerts\launcher.py"
$icon = "$scriptRoot\icons\snapalert.ico"
$startMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\SnapAlert"
$customAlertsFile = "$scriptRoot\data\custom_alerts.json"

# Create SnapAlert folder in Start Menu if it doesn't exist
if (-not (Test-Path $startMenu)) {
    New-Item -ItemType Directory -Path $startMenu -Force | Out-Null
}

function New-SnapAlertShortcut($name, $alertId, $description = "") {
    $shortcutPath = "$startMenu\$name.lnk"
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = $python
    $Shortcut.Arguments = "`"$launcher`" `"$alertId`""
    $Shortcut.WorkingDirectory = $scriptRoot
    $Shortcut.Description = $description
    
    # Use icon if it exists
    if (Test-Path $icon) {
        $Shortcut.IconLocation = $icon
    }
    
    $Shortcut.Save()
    Write-Host "Created shortcut: $name"
}

# Check if custom alerts file exists
if (-not (Test-Path $customAlertsFile)) {
    Write-Host "ERROR: Custom alerts file not found: $customAlertsFile"
    Write-Host "Please create some custom alerts in the SnapAlert web interface first."
    exit 1
}

# Read and parse custom alerts JSON
try {
    $customAlertsContent = Get-Content $customAlertsFile -Raw
    $customAlerts = $customAlertsContent | ConvertFrom-Json
} catch {
    Write-Host "ERROR: Error reading custom alerts file: $($_.Exception.Message)"
    exit 1
}

# Filter enabled alerts
$enabledAlerts = $customAlerts | Where-Object { $_.enabled -eq $true }

if ($enabledAlerts.Count -eq 0) {
    Write-Host "WARNING: No enabled custom alerts found."
    Write-Host "Please enable some alerts in the SnapAlert web interface first."
    exit 1
}

Write-Host "SnapAlert Shortcut Generator"
Write-Host "Found $($enabledAlerts.Count) enabled custom alerts"
Write-Host ""

# Create shortcuts for each enabled alert
foreach ($alert in $enabledAlerts) {
    $alertName = $alert.name
    $alertId = $alert.id
    $alertMessage = $alert.message
    
    # Create a clean shortcut name
    $shortcutName = "SnapAlert - $alertName"
    
    # Create description with alert details
    $description = "SnapAlert Custom Alert: $alertMessage"
    
    New-SnapAlertShortcut -name $shortcutName -alertId $alertId -description $description
}

Write-Host ""
Write-Host "Successfully created $($enabledAlerts.Count) shortcuts in:"
Write-Host "   $startMenu"
Write-Host ""
Write-Host "You can now:"
Write-Host "- Find shortcuts in Start Menu under SnapAlert"
Write-Host "- Pin them to taskbar or desktop"
Write-Host "- Use them to trigger custom alerts manually"
Write-Host ""
Write-Host "Note: Shortcuts will only work for enabled alerts."
Write-Host "If you disable an alert, the shortcut will show an error."

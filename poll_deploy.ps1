$apiKey = "rnd_1K6jk4R8frhWY3aSJcRAxa7W88vt"
$serviceId = "srv-d4rfik75r7bs73f7ungg"
$headers = @{
    "Authorization" = "Bearer $apiKey"
}

$uri = "https://api.render.com/v1/services/$serviceId/deploys"

Write-Output "Checking latest deploy status..."
$final = $null
for ($i = 0; $i -lt 60; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri $uri -Headers $headers -Method GET
        if ($resp -and $resp.Count -gt 0) {
            $latest = $resp[0].deploy
            $status = $latest.status
            Write-Output "Poll #$($i+1): Status=$status (ID: $($latest.id.Substring(0,8)))"
            
            if ($status -in @('live', 'failed', 'cancelled')) {
                $final = $status
                break
            }
        }
    } catch {
        Write-Output "Error polling: $_"
        break
    }
    Start-Sleep -Seconds 5
}

if ($null -eq $final) {
    Write-Output "Timeout waiting for deploy"
} else {
    Write-Output "FINAL_STATUS: $final"
    if ($final -eq 'live') {
        Write-Output "Deploy succeeded and is live!"
    } else {
        Write-Output "Deploy ended with status: $final"
    }
}

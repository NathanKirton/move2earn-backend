$apiKey = "rnd_1K6jk4R8frhWY3aSJcRAxa7W88vt"
$serviceId = "srv-d4rfik75r7bs73f7ungg"
$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

$uri = "https://api.render.com/v1/services/$serviceId/deploys"

try {
    Write-Output "Creating deploy..."
    $response = Invoke-RestMethod -Uri $uri -Headers $headers -Method POST -Body "{}"
    Write-Output "Deploy ID: $($response.deploy.id)"
    Write-Output "Status: $($response.deploy.status)"
    Write-Output "Commit: $($response.deploy.commit.id)"
} catch {
    Write-Output "Error: $_"
}

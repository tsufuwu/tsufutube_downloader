# Generate Self-Signed Certificate
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Tsufutube Downloader" -CertStoreLocation Cert:\CurrentUser\My

# Basic Password
$password = ConvertTo-SecureString -String "Tsufutube2024" -Force -AsPlainText

# Export to PFX
$pfxPath = "$PSScriptRoot\Tsufutube_SelfSigned.pfx"
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password

Write-Host "Certificate generated at: $pfxPath" -ForegroundColor Green
Write-Host "Password: Tsufutube2024" -ForegroundColor Yellow

# Convert to Base64 for GitHub Secret
$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($pfxPath))
$base64Path = "$PSScriptRoot\cert_base64.txt"
[IO.File]::WriteAllText($base64Path, $base64)

Write-Host "`n--- FOR GITHUB SECRETS ---" -ForegroundColor Cyan
Write-Host "1. Open repo Settings -> Secrets and variables -> Actions"
Write-Host "2. Create 'SIGNING_CERT' and paste content from: $base64Path"
Write-Host "3. Create 'SIGNING_PASSWORD' with value: Tsufutube2024"
Write-Host "---------------------------"

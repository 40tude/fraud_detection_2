# Function to display directory tree with excluded directories
# Example of calling the function
# . .\Get-Tree.ps1  
# Get-Tree -Path "C:\Votre\Dossier" -Exclude ".mypy_cache", "mlruns"
function Get-Tree {
    param (
        [string]$Path = ".",
        [int]$Level = 0,
        [string[]]$Exclude = @()  # List of directories to exclude
    )
    
    # Get directories and files, excluding specified directories
    $items = Get-ChildItem -Path $Path -Force | Where-Object {
        -not ($Exclude -contains $_.Name)
    }

    foreach ($item in $items) {
        Write-Host (" " * $Level) + "|-- " + $item.Name
        if ($item.PSIsContainer) {
            # Recursively call function for subdirectories
            Get-Tree -Path $item.FullName -Level ($Level + 2) -Exclude $Exclude
        }
    }
}


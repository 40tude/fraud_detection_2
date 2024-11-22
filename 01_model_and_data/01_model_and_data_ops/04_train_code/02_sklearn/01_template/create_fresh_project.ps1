# Delete a directory recursively if it exists
function Delete-Directory {
    param (
        [string]$directoryPath
    )
    if (Test-Path $directoryPath) {
        Remove-Item -Recurse -Force $directoryPath
        Write-Output "Directory '$directoryPath' has been deleted."
    } else {
        Write-Output "Directory '$directoryPath' does not exist."
    }
}

# Delete a file if it exists
function Delete-File {
    param (
        [string]$filePath
    )
    if (Test-Path $filePath) {
        Remove-Item -Force $filePath
        Write-Output "File '$filePath' has been deleted."
    } else {
        Write-Output "File '$filePath' does not exist."
    }
}

# Paths to the directories and files to delete
$assetsPath = "./assets"
$imgPath = "./img"
$readmeFile = "./readme.md"
$trainLogFile = "./train.log"

# Delete directories
Delete-Directory -directoryPath $assetsPath
Delete-Directory -directoryPath $imgPath

# Delete files
Delete-File -filePath $readmeFile
Delete-File -filePath $trainLogFile

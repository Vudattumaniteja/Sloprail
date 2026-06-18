Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

py -m unittest discover -s "$PSScriptRoot\..\tests"
py "$PSScriptRoot\validate_project.py"

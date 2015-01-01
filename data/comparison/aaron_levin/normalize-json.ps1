# This script takes Aaron Levin's results file (in original_results.txt) and transforms it into results.txt.
# The original file contains multiple lines per JSon object.
# This causes problems for the comparison.py script, which expects one JSon object per line.
# The results.txt file fixes this.
# 
# Additionally there were some extra double quotes that made the json invalid. 
# These have also been removed.
# 
# Note: Run this Powershell script from within the "aaron_levin" folder.

$inputPath = resolve-path './original_results.txt'
$contents = [IO.File]::ReadAllText($inputPath.Path)

$splitter = '"]}'  # Each JSon object ends with these characters
[string[]] $splitters = @($splitter)
$jsonBlocks = $contents.Split($splitter, [StringSplitOptions]::None)

# Remove newline characters and extraneous double quotes:
[string[]] $singleLineJsonBlocks = $jsonBlocks | % { $_ -replace "(`r`n|`r|`n)",'' -replace '"{"title"','{"title"' }
$normalizedResults = [String]::Join( $splitter + "`r`n", $singleLineJsonBlocks ) -replace '"}"','"}'

$outputPath = resolve-path './results.txt'
$utf8EncodingWithoutBom = new-object System.Text.Utf8Encoding -argumentList $false
[IO.File]::WriteAllText( $outputPath.Path, $normalizedResults, $utf8EncodingWithoutBom )

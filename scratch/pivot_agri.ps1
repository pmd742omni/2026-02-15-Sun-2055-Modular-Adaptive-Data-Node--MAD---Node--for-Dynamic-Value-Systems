$ErrorActionPreference = "Stop"

# Define version directory path
$dir = "c:\Users\ignaz\OneDrive\Documents\Projects\2026-02-15 Sun 2055 Modular Adaptive Data Node (MAD - Node) for Dynamic Value Systems\2026-03-30 Mon 0833 Chapters\2026-05-13 Wed 1220 Version 2026-05-13 Wed 1246"

# 1. 1.1 Background of the Study.txt
$path = Join-Path $dir "1.1 Background of the Study.txt"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("insights to enhance crop yields;", "insights to optimize irrigation schedules and manage soil hydration;")
[System.IO.File]::WriteAllText($path, $text)

# 2. 1.2 Problem Statement.txt
$path = Join-Path $dir "1.2 Problem Statement.txt"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("a lack of localized, microclimate-specific data processing for yield optimization;", "a lack of localized, microclimate-specific data processing to determine watering requirements and manage soil hydration;")
[System.IO.File]::WriteAllText($path, $text)

# 3. 1.3 Aim of the Project.txt
$path = Join-Path $dir "1.3 Aim of the Project.txt"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("provide actionable solutions for agricultural yield optimization,", "provide actionable solutions for localized soil moisture optimization and watering requirement determination,")
[System.IO.File]::WriteAllText($path, $text)

# 4. 1.4 Objectives of the Project.txt
$path = Join-Path $dir "1.4 Objectives of the Project.txt"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("process this data through a localized TensorFlow Lite yield prediction model,", "process this data through a localized TensorFlow Lite irrigation prediction model (to determine watering requirements),")
[System.IO.File]::WriteAllText($path, $text)

# 5. 1.5 Research Questions.txt
$path = Join-Path $dir "1.5 Research Questions.txt"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("accuracy of agricultural yield predictions", "accuracy of localized irrigation and watering requirement predictions")
[System.IO.File]::WriteAllText($path, $text)

# 6. 1.6 Scope of the Project.txt
$path = Join-Path $dir "1.6 Scope of the Project.txt"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("and TensorFlow Lite yield modeling", "and TensorFlow Lite irrigation and watering requirement modeling")
[System.IO.File]::WriteAllText($path, $text)

# 7. 1.7 Significance of the Study.txt
$path = Join-Path $dir "1.7 Significance of the Study.txt"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("actionable planting and yield predictions", "actionable soil hydration and watering requirement predictions")
[System.IO.File]::WriteAllText($path, $text)

# 8. 2.2 Theoretical Background.md
$path = Join-Path $dir "2026-05-11 0818 2.2 Theoretical Background.md"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("such as TensorFlow Lite for agricultural yield prediction,", "such as TensorFlow Lite for agricultural irrigation and watering requirement prediction,")
[System.IO.File]::WriteAllText($path, $text)

# 9. 2.5 Gaps in Existing Solutions.md
$path = Join-Path $dir "2026-05-11 0836 2.5 Gaps in Existing Solutions.md"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("data processing for yield optimization [11].", "data processing for soil hydration and irrigation optimization [11].")
$text = $text.Replace("precise, microclimate-specific insights to enhance crop yields,", "precise, microclimate-specific insights to manage soil moisture levels and determine watering needs,")
[System.IO.File]::WriteAllText($path, $text)

# 10. 3.3 System Requirements.md
$path = Join-Path $dir "2026-05-27 0832 3.3 System Requirements.md"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("present analytical data (such as farm yield projections and market transaction metrics)", "present analytical data (such as soil moisture analytics and irrigation/watering alerts)")
$text = $text.Replace("| **Machine Learning**| TensorFlow Lite Runtime | Local crop yield prediction inference | Pi 4 Hub |", "| **Machine Learning**| TensorFlow Lite Runtime | Local irrigation/watering requirement inference | Pi 4 Hub |")
$text = $text.Replace("execute low-latency predictive analysis on localized yield variables", "execute low-latency predictive analysis on localized soil moisture and watering requirements")
[System.IO.File]::WriteAllText($path, $text)

# 11. 3.4 System Design.md
$path = Join-Path $dir "2026-05-29 1355 3.4 System Design.md"
$text = [System.IO.File]::ReadAllText($path)
$text = $text.Replace("executes a TensorFlow Lite crop model", "executes a TensorFlow Lite watering requirements predictor model")
$text = $text.Replace("Predict[Load TF Lite crop yield predictor model]", "Predict[Load TF Lite irrigation/watering predictor model]")
[System.IO.File]::WriteAllText($path, $text)

Write-Host "Pivoted Agri-Analytics successfully!"

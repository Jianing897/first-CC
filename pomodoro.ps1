# ============================================================
# Pomodoro Timer - 桌面番茄钟
# PowerShell + WPF  零依赖  双击或右键运行
# ============================================================
#Requires -Version 5.1

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName System.Windows.Forms

# ============================================================
# XAML
# ============================================================
[xml]$xaml = @'
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="番茄钟" Height="430" Width="310"
    ResizeMode="CanMinimize" WindowStartupLocation="CenterScreen"
    Topmost="True" Background="#F5F6FA">

    <Grid Margin="18">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <!-- 模式标签 -->
        <Border x:Name="ModeBadge" Grid.Row="0"
                CornerRadius="10" Padding="14,6"
                HorizontalAlignment="Center" Margin="0,0,0,12"
                Background="#E74C3C">
            <TextBlock x:Name="ModeLabel" Text="FOCUS"
                       FontSize="16" FontWeight="Bold"
                       Foreground="White"
                       HorizontalAlignment="Center"/>
        </Border>

        <!-- 倒计时 -->
        <Border Grid.Row="1" CornerRadius="14" Padding="16"
                Background="White" Margin="0,0,0,8">
            <Border.Effect>
                <DropShadowEffect BlurRadius="8" ShadowDepth="2" Opacity="0.1"/>
            </Border.Effect>
            <TextBlock x:Name="TimerText" Text="25:00"
                       FontSize="60" FontWeight="Bold"
                       Foreground="#2C3E50"
                       HorizontalAlignment="Center"
                       FontFamily="Consolas"/>
        </Border>

        <!-- 进度条 -->
        <ProgressBar x:Name="TimerProgress" Grid.Row="2"
                     Height="8" Margin="0,4,0,8"
                     Minimum="0" Maximum="100" Value="0"
                     Foreground="#E74C3C" Background="#E8E8E8"/>

        <!-- 番茄计数 -->
        <StackPanel Grid.Row="3" HorizontalAlignment="Center"
                    Orientation="Horizontal" Margin="0,6,0,10">
            <TextBlock x:Name="CountText" Text="0"
                       FontSize="22" FontWeight="Bold"
                       Foreground="#E74C3C"/>
            <TextBlock Text=" / today" FontSize="16"
                       Foreground="#999" VerticalAlignment="Center"
                       Margin="4,0,0,0"/>
        </StackPanel>

        <!-- 按钮 -->
        <WrapPanel Grid.Row="4" HorizontalAlignment="Center">
            <Button x:Name="BtnStart" Content="START"
                    Width="115" Height="44" Margin="5"
                    FontSize="16" FontWeight="Bold"
                    Foreground="White" Background="#E74C3C"
                    BorderThickness="0" Cursor="Hand"/>
            <Button x:Name="BtnPause" Content="PAUSE"
                    Width="115" Height="44" Margin="5"
                    FontSize="16" FontWeight="Bold"
                    Foreground="White" Background="#F39C12"
                    BorderThickness="0" Cursor="Hand"/>
            <Button x:Name="BtnReset" Content="RESET"
                    Width="85" Height="36" Margin="4"
                    FontSize="14" Foreground="#555"
                    Background="#EEE" BorderBrush="#CCC"
                    BorderThickness="1" Cursor="Hand"/>
            <Button x:Name="BtnSkip" Content="SKIP"
                    Width="85" Height="36" Margin="4"
                    FontSize="14" Foreground="#555"
                    Background="#EEE" BorderBrush="#CCC"
                    BorderThickness="1" Cursor="Hand"/>
            <Button x:Name="BtnPin" Content="PIN"
                    Width="60" Height="36" Margin="4"
                    FontSize="13" Foreground="White"
                    Background="#3498DB" BorderThickness="0" Cursor="Hand"/>
        </WrapPanel>
    </Grid>
</Window>
'@

# ============================================================
# Load Window
# ============================================================
$reader = New-Object System.Xml.XmlNodeReader $xaml
$Window = [Windows.Markup.XamlReader]::Load($reader)

# Get controls
$TimerText    = $Window.FindName("TimerText")
$TimerProgress = $Window.FindName("TimerProgress")
$ModeBadge    = $Window.FindName("ModeBadge")
$ModeLabel    = $Window.FindName("ModeLabel")
$CountText    = $Window.FindName("CountText")

$BtnStart = $Window.FindName("BtnStart")
$BtnPause = $Window.FindName("BtnPause")
$BtnReset = $Window.FindName("BtnReset")
$BtnSkip  = $Window.FindName("BtnSkip")
$BtnPin   = $Window.FindName("BtnPin")

# ============================================================
# State
# ============================================================
$script:RemainingSeconds = 25 * 60
$script:TotalSeconds     = 25 * 60
$script:IsRunning        = $false
$script:CurrentMode      = "Focus"
$script:CompletedCount   = 0
$script:TodayTotal       = 0
$script:IsPinned         = $true

$FocusDuration      = 25 * 60
$ShortBreakDuration = 5 * 60
$LongBreakDuration  = 15 * 60

# ============================================================
# Data persistence
# ============================================================
$DataDir  = "$env:LOCALAPPDATA\PomodoroApp"
$DataFile = "$DataDir\today.json"

function Load-Data {
    if (-not (Test-Path $DataFile)) { $script:TodayTotal = 0; return }
    try {
        $d = Get-Content $DataFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($d.date -eq (Get-Date).ToString("yyyy-MM-dd")) {
            $script:TodayTotal = $d.count
        } else {
            $script:TodayTotal = 0
        }
    } catch { $script:TodayTotal = 0 }
    $CountText.Text = $script:TodayTotal.ToString()
}

function Save-Data {
    if (-not (Test-Path $DataDir)) {
        New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
    }
    @{ date = (Get-Date).ToString("yyyy-MM-dd"); count = $script:TodayTotal } |
        ConvertTo-Json -Compress |
        Set-Content -Path $DataFile -Force -Encoding UTF8
}

# ============================================================
# Display helpers
# ============================================================
function Format-Time {
    param([int]$Seconds)
    $t = [TimeSpan]::FromSeconds($Seconds)
    return "{0:D2}:{1:D2}" -f $t.Minutes, $t.Seconds
}

function Set-Colors {
    param([string]$Mode)
    if ($Mode -eq "Focus") {
        $ModeBadge.Background     = "#E74C3C"
        $ModeLabel.Text           = "FOCUS"
        $TimerProgress.Foreground = "#E74C3C"
        $BtnStart.Background      = "#E74C3C"
    } elseif ($Mode -eq "ShortBreak") {
        $ModeBadge.Background     = "#27AE60"
        $ModeLabel.Text           = "BREAK"
        $TimerProgress.Foreground = "#27AE60"
        $BtnStart.Background      = "#27AE60"
    } else {
        $ModeBadge.Background     = "#2980B9"
        $ModeLabel.Text           = "LONG BREAK"
        $TimerProgress.Foreground = "#2980B9"
        $BtnStart.Background      = "#2980B9"
    }
}

function Update-Display {
    $TimerText.Text = Format-Time $script:RemainingSeconds
    $pct = [Math]::Max(0, ($script:RemainingSeconds / $script:TotalSeconds) * 100)
    $TimerProgress.Value = $pct
    $CountText.Text = $script:TodayTotal.ToString()
}

function Set-ButtonStates {
    $BtnStart.IsEnabled = (-not $script:IsRunning)
    $BtnPause.IsEnabled = $script:IsRunning
    $BtnSkip.IsEnabled  = (-not $script:IsRunning)
}

# ============================================================
# Timer tick
# ============================================================
$timer = New-Object System.Windows.Threading.DispatcherTimer
$timer.Interval = [TimeSpan]::FromSeconds(1)
$timer.Add_Tick({
    try {
        if (-not $script:IsRunning) { return }
        $script:RemainingSeconds -= 1
        Update-Display

        if ($script:RemainingSeconds -le 0) {
            $script:IsRunning = $false
            $timer.Stop()
            Set-ButtonStates
            On-Finish
        }
    } catch {
        [System.Windows.Forms.MessageBox]::Show(
            "Timer error: $($_.Exception.Message)", "Error", "OK", "Error")
    }
})

# ============================================================
# Mode switch & finish
# ============================================================
function Switch-To {
    param([string]$Mode)
    $script:IsRunning = $false
    $script:CurrentMode = $Mode
    Set-Colors -Mode $Mode
    if ($Mode -eq "Focus") {
        $script:RemainingSeconds = $FocusDuration
        $script:TotalSeconds = $FocusDuration
    } elseif ($Mode -eq "ShortBreak") {
        $script:RemainingSeconds = $ShortBreakDuration
        $script:TotalSeconds = $ShortBreakDuration
    } else {
        $script:RemainingSeconds = $LongBreakDuration
        $script:TotalSeconds = $LongBreakDuration
    }
    Update-Display
    Set-ButtonStates
}

function On-Finish {
    $mode = $script:CurrentMode
    # Beep
    try { [System.Media.SystemSounds]::Beep.Play() } catch {}
    try { [System.Media.SystemSounds]::Asterisk.Play() } catch {}

    if ($mode -eq "Focus") {
        $script:CompletedCount += 1
        $script:TodayTotal += 1
        Save-Data
        Update-Display
        $next = if ($script:CompletedCount -ge 4) {
            $script:CompletedCount = 0
            "LongBreak"
        } else {
            "ShortBreak"
        }
        [System.Windows.Forms.MessageBox]::Show(
            "Done! Total today: $($script:TodayTotal)", "Pomodoro", "OK", "Information")
        Switch-To -Mode $next
    } else {
        [System.Windows.Forms.MessageBox]::Show(
            "Break over! Let's go.", "Pomodoro", "OK", "Information")
        Switch-To -Mode "Focus"
    }
    $timer.Start()
}

# ============================================================
# Button actions
# ============================================================
$BtnStart.Add_Click({
    $script:IsRunning = $true
    Set-ButtonStates
})

$BtnPause.Add_Click({
    $script:IsRunning = $false
    Set-ButtonStates
})

$BtnReset.Add_Click({
    $script:IsRunning = $false
    if ($script:CurrentMode -eq "Focus") {
        $script:RemainingSeconds = $FocusDuration
        $script:TotalSeconds = $FocusDuration
    } elseif ($script:CurrentMode -eq "ShortBreak") {
        $script:RemainingSeconds = $ShortBreakDuration
        $script:TotalSeconds = $ShortBreakDuration
    } else {
        $script:RemainingSeconds = $LongBreakDuration
        $script:TotalSeconds = $LongBreakDuration
    }
    Update-Display
    Set-ButtonStates
})

$BtnSkip.Add_Click({
    $script:IsRunning = $false
    $script:RemainingSeconds = 0
    Set-ButtonStates
    On-Finish
})

$BtnPin.Add_Click({
    $script:IsPinned = (-not $script:IsPinned)
    $Window.Topmost = $script:IsPinned
    $BtnPin.Background = if ($script:IsPinned) { "#3498DB" } else { "#95A5A6" }
})

# ============================================================
# Keyboard shortcuts
# ============================================================
$Window.Add_KeyDown({
    param($sender, $e)
    if ($e.Key -eq "Space") {
        if ($script:IsRunning) { $BtnPause.RaiseEvent((New-Object System.Windows.RoutedEventArgs([System.Windows.Controls.Button]::ClickEvent))) }
        else { $BtnStart.RaiseEvent((New-Object System.Windows.RoutedEventArgs([System.Windows.Controls.Button]::ClickEvent))) }
    }
    if ($e.Key -eq "R") {
        $BtnReset.RaiseEvent((New-Object System.Windows.RoutedEventArgs([System.Windows.Controls.Button]::ClickEvent)))
    }
    if ($e.Key -eq "S") {
        $BtnSkip.RaiseEvent((New-Object System.Windows.RoutedEventArgs([System.Windows.Controls.Button]::ClickEvent)))
    }
    if ($e.Key -eq "P") {
        $BtnPin.RaiseEvent((New-Object System.Windows.RoutedEventArgs([System.Windows.Controls.Button]::ClickEvent)))
    }
})

# ============================================================
# Window close
# ============================================================
$Window.Add_Closing({
    $script:IsRunning = $false
    $timer.Stop()
    Save-Data
})

# ============================================================
# Start
# ============================================================
Load-Data
Set-Colors -Mode "Focus"
Update-Display
Set-ButtonStates
$timer.Start()

Write-Host "Pomodoro started. Space=Start/Pause R=Reset S=Skip P=Pin"

$Window.ShowDialog() | Out-Null
$timer.Stop()
Write-Host "Pomodoro closed. Today: $($script:TodayTotal)"

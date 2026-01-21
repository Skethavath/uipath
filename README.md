# UiPath Job Automation

Automate running UiPath jobs using Playwright browser automation. This script simulates user interactions with the UiPath Assistant or Orchestrator web UI to trigger job execution.

## Features

- **Command-line interface**: Run specific jobs via CLI arguments
- **Configuration-based**: Store job names and credentials in config
- **Error handling**: Robust error detection and reporting
- **Logging**: Track execution history
- **Headless option**: Run with or without visible browser
- **Session management**: Handle authentication tokens/cookies
- **Job discovery**: List all available jobs
- **Multiple jobs**: Run one or more jobs in sequence

## Prerequisites

- Python 3.7 or higher
- UiPath account with access to jobs/processes
- Playwright browser binaries

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers**:
   ```bash
   playwright install
   ```

3. **Configure credentials**:
   
   Option A: Create a `.env` file (recommended):
   ```bash
   cp env.example.txt .env
   ```
   Then edit `.env` and add your credentials:
   ```
   UIPATH_URL=https://platform.uipath.com
   UIPATH_USERNAME=your_username
   UIPATH_PASSWORD=your_password
   ```

   Option B: Set environment variables:
   ```bash
   export UIPATH_URL=https://platform.uipath.com
   export UIPATH_USERNAME=your_username
   export UIPATH_PASSWORD=your_password
   ```

   Option C: Edit `config.json` directly (less secure):
   ```json
   {
     "uipath": {
       "url": "https://platform.uipath.com"
     }
   }
   ```

## Usage

### List Available Jobs

```bash
python uipath_automation.py --list-jobs
```

This will display all available jobs/processes that can be run.

### Run a Single Job

```bash
python uipath_automation.py --job "Process Name"
```

Replace `"Process Name"` with the exact name of your job/process as it appears in UiPath.

### Run Multiple Jobs

```bash
python uipath_automation.py --job "Job 1" --job "Job 2" --job "Job 3"
```

### Run All Jobs

```bash
python uipath_automation.py --all
```

This will attempt to run all jobs found on the jobs page.

### Headless Mode

Run without opening a visible browser window:

```bash
python uipath_automation.py --job "Process Name" --headless
```

### Custom Configuration File

```bash
python uipath_automation.py --config my_config.json --job "Process Name"
```

## Configuration

### config.json

The configuration file supports the following settings:

```json
{
  "uipath": {
    "url": "https://platform.uipath.com",
    "timeout": 30000
  },
  "browser": {
    "headless": false,
    "slow_mo": 0
  },
  "jobs": {
    "default_folder": "",
    "known_jobs": []
  }
}
```

- `uipath.url`: Base URL for UiPath platform
- `uipath.timeout`: Timeout in milliseconds for page operations
- `browser.headless`: Run browser in headless mode (true/false)
- `browser.slow_mo`: Slow down operations by specified milliseconds (useful for debugging)

## Environment Variables

- `UIPATH_URL`: UiPath platform URL
- `UIPATH_USERNAME`: Your UiPath username
- `UIPATH_PASSWORD`: Your UiPath password
- `HEADLESS`: Set to `true` to run in headless mode
- `BROWSER_TIMEOUT`: Timeout in milliseconds (default: 30000)

## Authentication

The script attempts to automatically log in using provided credentials. If automatic login fails:

1. The browser window will remain open
2. You can manually log in
3. Press Enter in the terminal to continue
4. The script will proceed with job execution

## Troubleshooting

### Login Issues

If automatic login doesn't work:

1. Check your credentials in `.env` or environment variables
2. Verify the UiPath URL is correct
3. Try logging in manually when the browser opens
4. Check if your organization uses SSO (may require manual login)

### Job Not Found

If a job cannot be found:

1. Use `--list-jobs` to see available job names
2. Ensure the job name matches exactly (case-sensitive)
3. Check that you have permissions to view/run the job
4. Verify you're in the correct folder/environment in UiPath

### Page Structure Changes

UiPath may update their UI, which could break the automation. If this happens:

1. Check the screenshot files generated:
   - `jobs_page_debug.png`: Screenshot of jobs page
   - `error_screenshot.png`: Screenshot on error
2. Update the selectors in `uipath_automation.py` if needed
3. Report the issue with the screenshots for assistance

### Debugging

Enable detailed logging by checking `uipath_automation.log`:

```bash
tail -f uipath_automation.log
```

The script saves screenshots when errors occur or when jobs cannot be found, which helps with debugging.

## Examples

### Example 1: Run a daily report job

```bash
python uipath_automation.py --job "Daily Sales Report"
```

### Example 2: Run multiple jobs in sequence

```bash
python uipath_automation.py --job "Extract Data" --job "Transform Data" --job "Load Data"
```

### Example 3: Schedule with Windows Task Scheduler

1. Create a batch file `run_job.bat`:
   ```batch
   @echo off
   cd C:\path\to\uipath\automation
   python uipath_automation.py --job "Scheduled Job"
   ```

2. Create a scheduled task in Windows Task Scheduler pointing to the batch file

### Example 4: Use in PowerShell script

```powershell
# run_jobs.ps1
$jobs = @("Job 1", "Job 2", "Job 3")
foreach ($job in $jobs) {
    python uipath_automation.py --job $job
    Start-Sleep -Seconds 5
}
```

## Logging

All operations are logged to:
- Console output (stdout)
- `uipath_automation.log` file

Logs include:
- Authentication status
- Job discovery results
- Job execution status
- Errors and warnings
- Timestamps for all operations

## Security Notes

- **Never commit `.env` file**: It contains sensitive credentials
- Store credentials securely: Use environment variables or secure credential managers
- Review logs: They may contain sensitive information
- Use least privilege: Ensure the account has only necessary permissions

## Limitations

- **UI-dependent**: This solution relies on UI automation, making it vulnerable to UI changes
- **Slower than API**: Browser automation is slower than direct API calls
- **Session management**: May require re-authentication if sessions expire
- **Concurrent execution**: Running multiple instances simultaneously may cause conflicts

## Alternative Solutions

If you have API access, consider using:
- UiPath Orchestrator REST API (more reliable and faster)
- UiPath Python SDK (`uipath-python`)
- UiRobot.exe CLI (if available locally)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files
3. Check generated screenshot files
4. Verify your UiPath environment and permissions

## License

This script is provided as-is for automation purposes.

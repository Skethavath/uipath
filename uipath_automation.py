#!/usr/bin/env python3
"""
UiPath Job Automation Script
Automates running UiPath jobs using Playwright browser automation.
"""

import json
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
except ImportError:
    print("Error: playwright is not installed. Please run: pip install -r requirements.txt")
    print("Then run: playwright install")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('uipath_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class UiPathAutomation:
    """Main class for UiPath job automation using Playwright."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the automation with configuration."""
        self.config = self._load_config(config_path)
        self.url = os.getenv('UIPATH_URL', self.config.get('uipath', {}).get('url', 'https://platform.uipath.com'))
        self.username = os.getenv('UIPATH_USERNAME', '')
        self.password = os.getenv('UIPATH_PASSWORD', '')
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        if 'browser' in self.config:
            self.headless = self.config['browser'].get('headless', self.headless)
        
        self.timeout = int(os.getenv('BROWSER_TIMEOUT', 
                                     self.config.get('uipath', {}).get('timeout', 30000)))
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"Could not load config file: {e}. Using defaults.")
            return {}
    
    def start_browser(self):
        """Start the browser instance."""
        logger.info("Starting browser...")
        self.playwright = sync_playwright().start()
        
        browser_type = self.playwright.chromium
        self.browser = browser_type.launch(
            headless=self.headless,
            slow_mo=self.config.get('browser', {}).get('slow_mo', 0)
        )
        
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        logger.info("Browser started successfully")
    
    def login(self) -> bool:
        """Handle login to UiPath platform."""
        logger.info(f"Navigating to {self.url}...")
        
        try:
            self.page.goto(self.url)
            self.page.wait_for_load_state('networkidle')
            
            # Check if we're already logged in
            if self._is_logged_in():
                logger.info("Already logged in")
                return True
            
            # Attempt to find and fill login form
            if self.username and self.password:
                logger.info("Attempting to log in...")
                
                # Common selectors for UiPath login
                username_selectors = [
                    'input[name="email"]',
                    'input[name="username"]',
                    'input[type="email"]',
                    'input[type="text"][placeholder*="email" i]',
                    'input[placeholder*="username" i]'
                ]
                
                password_selectors = [
                    'input[name="password"]',
                    'input[type="password"]'
                ]
                
                login_button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Sign in")',
                    'button:has-text("Login")',
                    'button:has-text("Log in")',
                    'input[type="submit"]'
                ]
                
                # Try to find and fill username
                username_filled = False
                for selector in username_selectors:
                    try:
                        if self.page.locator(selector).is_visible(timeout=2000):
                            self.page.fill(selector, self.username)
                            username_filled = True
                            logger.info(f"Filled username using selector: {selector}")
                            break
                    except:
                        continue
                
                if not username_filled:
                    logger.warning("Could not find username field. You may need to log in manually.")
                    return False
                
                # Try to find and fill password
                password_filled = False
                for selector in password_selectors:
                    try:
                        if self.page.locator(selector).is_visible(timeout=2000):
                            self.page.fill(selector, self.password)
                            password_filled = True
                            logger.info(f"Filled password")
                            break
                    except:
                        continue
                
                if not password_filled:
                    logger.warning("Could not find password field.")
                    return False
                
                # Try to click login button
                login_clicked = False
                for selector in login_button_selectors:
                    try:
                        if self.page.locator(selector).is_visible(timeout=2000):
                            self.page.click(selector)
                            login_clicked = True
                            logger.info(f"Clicked login button using selector: {selector}")
                            break
                    except:
                        continue
                
                if not login_clicked:
                    logger.warning("Could not find login button. Trying to press Enter...")
                    self.page.keyboard.press('Enter')
                
                # Wait for navigation after login
                self.page.wait_for_load_state('networkidle', timeout=10000)
                
                if self._is_logged_in():
                    logger.info("Login successful")
                    return True
                else:
                    logger.warning("Login may have failed. Check credentials.")
                    return False
            else:
                logger.warning("No credentials provided. Please log in manually or set UIPATH_USERNAME and UIPATH_PASSWORD")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def _is_logged_in(self) -> bool:
        """Check if user is logged in by looking for common UI elements."""
        try:
            # Common indicators of being logged in
            logged_in_indicators = [
                'text=Jobs',
                'text=Processes',
                'text=Robots',
                'text=Orchestrator',
                '[data-testid*="menu"]',
                'nav',
                '[role="navigation"]'
            ]
            
            for indicator in logged_in_indicators:
                try:
                    if self.page.locator(indicator).is_visible(timeout=2000):
                        return True
                except:
                    continue
            
            # Check for login page indicators
            login_indicators = [
                'text=Sign in',
                'text=Login',
                'input[type="password"]'
            ]
            
            for indicator in login_indicators:
                try:
                    if self.page.locator(indicator).is_visible(timeout=1000):
                        return False
                except:
                    continue
            
            # If we can't determine, assume logged in if we're not on a login page
            return True
            
        except Exception as e:
            logger.debug(f"Could not determine login status: {e}")
            return False
    
    def navigate_to_jobs(self):
        """Navigate to the Jobs or Processes page."""
        logger.info("Navigating to jobs page...")
        
        try:
            # Common navigation patterns
            job_links = [
                'a:has-text("Jobs")',
                'a:has-text("Processes")',
                'a[href*="/jobs"]',
                'a[href*="/processes"]',
                'button:has-text("Jobs")',
                'button:has-text("Processes")'
            ]
            
            for link_selector in job_links:
                try:
                    if self.page.locator(link_selector).is_visible(timeout=2000):
                        self.page.click(link_selector)
                        self.page.wait_for_load_state('networkidle')
                        logger.info(f"Clicked on jobs link: {link_selector}")
                        return
                except:
                    continue
            
            # If no link found, try direct navigation
            if '/jobs' in self.page.url or '/processes' in self.page.url:
                logger.info("Already on jobs page")
            else:
                logger.warning("Could not find jobs link. Attempting direct navigation...")
                self.page.goto(f"{self.url.rstrip('/')}/jobs")
                self.page.wait_for_load_state('networkidle')
                
        except Exception as e:
            logger.error(f"Error navigating to jobs: {e}")
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all available jobs/processes."""
        logger.info("Listing available jobs...")
        
        self.navigate_to_jobs()
        
        # Wait for jobs list to load
        self.page.wait_for_timeout(2000)
        
        jobs = []
        
        # Common selectors for job/process items
        job_item_selectors = [
            'tr[data-testid*="job"]',
            'tr[data-testid*="process"]',
            'div[data-testid*="job"]',
            'div[data-testid*="process"]',
            '.job-row',
            '.process-row',
            'tbody tr',
            '[class*="job"]',
            '[class*="process"]'
        ]
        
        # Try different strategies to find job items
        for selector in job_item_selectors:
            try:
                elements = self.page.locator(selector).all()
                if len(elements) > 0:
                    logger.info(f"Found {len(elements)} items using selector: {selector}")
                    
                    for i, element in enumerate(elements[:50]):  # Limit to first 50
                        try:
                            # Try to extract job name
                            name = element.locator('td:first-child, [class*="name"], [class*="title"]').first
                            if name.count() > 0:
                                job_name = name.inner_text().strip()
                                if job_name:
                                    jobs.append({
                                        'name': job_name,
                                        'index': i,
                                        'element': element
                                    })
                        except:
                            continue
                    
                    if jobs:
                        break
            except:
                continue
        
        # If no jobs found with structured selectors, try to get text content
        if not jobs:
            logger.warning("Could not find jobs using standard selectors. Page structure may be different.")
            logger.info("Page URL: " + self.page.url)
            logger.info("Saving page screenshot for debugging...")
            self.page.screenshot(path='jobs_page_debug.png')
        
        return jobs
    
    def run_job(self, job_name: str) -> bool:
        """Run a specific job by name."""
        logger.info(f"Attempting to run job: {job_name}")
        
        self.navigate_to_jobs()
        self.page.wait_for_timeout(2000)
        
        # Try to find the job and its play button
        # Common patterns for play/run buttons
        play_button_selectors = [
            f'button:has-text("{job_name}") + button[aria-label*="play" i]',
            f'button:has-text("{job_name}") + button[aria-label*="run" i]',
            f'tr:has-text("{job_name}") button[aria-label*="play" i]',
            f'tr:has-text("{job_name}") button[aria-label*="run" i]',
            f'[data-testid*="job"]:has-text("{job_name}") button:has-text("Play")',
            f'[data-testid*="job"]:has-text("{job_name}") button:has-text("Run")',
            f'button[title*="play" i]:near(:text="{job_name}")',
            f'button[title*="run" i]:near(:text="{job_name}")'
        ]
        
        # Also try finding by row first, then button in that row
        try:
            # Find row containing job name
            job_row = self.page.locator(f'tr:has-text("{job_name}"), div:has-text("{job_name}")').first
            
            if job_row.is_visible(timeout=5000):
                logger.info(f"Found job row for: {job_name}")
                
                # Look for play button in the row
                play_button = job_row.locator(
                    'button[aria-label*="play" i], '
                    'button[aria-label*="run" i], '
                    'button:has-text("Play"), '
                    'button:has-text("Run"), '
                    'button[title*="play" i], '
                    'button[title*="run" i], '
                    '[class*="play"], '
                    '[class*="run"]'
                ).first
                
                if play_button.is_visible(timeout=2000):
                    logger.info(f"Found play button for job: {job_name}")
                    play_button.click()
                    self.page.wait_for_timeout(2000)
                    logger.info(f"Successfully triggered job: {job_name}")
                    return True
                else:
                    logger.error(f"Could not find play button for job: {job_name}")
                    return False
            else:
                logger.error(f"Could not find job: {job_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error running job {job_name}: {e}")
            # Try alternative approach with direct selectors
            for selector in play_button_selectors:
                try:
                    if self.page.locator(selector).is_visible(timeout=2000):
                        self.page.click(selector)
                        self.page.wait_for_timeout(2000)
                        logger.info(f"Successfully triggered job using selector: {selector}")
                        return True
                except:
                    continue
            
            logger.error(f"Could not trigger job: {job_name}")
            return False
    
    def run_all_jobs(self) -> Dict[str, bool]:
        """Run all available jobs."""
        logger.info("Running all jobs...")
        jobs = self.list_jobs()
        results = {}
        
        for job in jobs:
            job_name = job['name']
            results[job_name] = self.run_job(job_name)
            self.page.wait_for_timeout(1000)  # Small delay between jobs
        
        return results
    
    def close(self):
        """Close the browser and cleanup."""
        logger.info("Closing browser...")
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")


def main():
    """Main entry point for command-line interface."""
    parser = argparse.ArgumentParser(
        description='Automate running UiPath jobs using Playwright',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python uipath_automation.py --job "My Process"
  python uipath_automation.py --list-jobs
  python uipath_automation.py --all
  python uipath_automation.py --job "Job1" --job "Job2"
        """
    )
    
    parser.add_argument(
        '--job',
        action='append',
        dest='jobs',
        help='Name of job(s) to run (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--list-jobs',
        action='store_true',
        help='List all available jobs'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all available jobs'
    )
    
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    args = parser.parse_args()
    
    # Initialize automation
    automation = UiPathAutomation(config_path=args.config)
    
    if args.headless:
        automation.headless = True
    
    try:
        # Start browser
        automation.start_browser()
        
        # Login
        if not automation.login():
            logger.error("Login failed. Please check credentials or log in manually.")
            print("\nBrowser will remain open for manual login. Press Enter after logging in...")
            input()
        
        # Handle different command options
        if args.list_jobs:
            jobs = automation.list_jobs()
            if jobs:
                print("\nAvailable Jobs:")
                print("-" * 50)
                for job in jobs:
                    print(f"  - {job['name']}")
                print(f"\nTotal: {len(jobs)} jobs found")
            else:
                print("\nNo jobs found. The page structure may be different.")
                print("Check 'jobs_page_debug.png' for a screenshot of the current page.")
        
        elif args.all:
            results = automation.run_all_jobs()
            print("\nJob Execution Results:")
            print("-" * 50)
            for job_name, success in results.items():
                status = "✓ Success" if success else "✗ Failed"
                print(f"  {status}: {job_name}")
        
        elif args.jobs:
            results = {}
            for job_name in args.jobs:
                success = automation.run_job(job_name)
                results[job_name] = success
                if success:
                    print(f"✓ Successfully triggered job: {job_name}")
                else:
                    print(f"✗ Failed to trigger job: {job_name}")
            
            print("\nSummary:")
            print("-" * 50)
            for job_name, success in results.items():
                status = "✓ Success" if success else "✗ Failed"
                print(f"  {status}: {job_name}")
        
        else:
            parser.print_help()
            print("\nPlease specify --job, --list-jobs, or --all")
        
        # Keep browser open for a moment if not headless
        if not automation.headless:
            print("\nBrowser will close in 5 seconds...")
            automation.page.wait_for_timeout(5000)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted by user")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nError: {e}")
        if automation.page:
            automation.page.screenshot(path='error_screenshot.png')
            print("Error screenshot saved as 'error_screenshot.png'")
    
    finally:
        automation.close()


if __name__ == '__main__':
    main()

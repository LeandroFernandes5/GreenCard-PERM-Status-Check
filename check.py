#!/usr/bin/env python3
import os
import json
import sys
import asyncio

from dotenv import load_dotenv

# Force load the injected variables
load_dotenv("/app/.env")

from playwright.async_api import async_playwright
from pushover_complete import PushoverAPI, PushoverCompleteError

PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
CASE_ID = os.getenv("CASE_ID", "G-100-25343-468220")


async def get_case_status():
    print("Opening headless browser...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        page = await context.new_page()

        # Variable to capture API response
        api_response = None

        # Route the API request to capture response
        async def handle_route(route, request):
            if "caseStatus" in request.url:
                await route.continue_()
                # Wait for response and capture it
                response = await request.response()
                if response:
                    try:
                        nonlocal api_response
                        api_response = await response.json()
                    except:
                        pass
            else:
                await route.continue_()

        await page.route("**/recaptcha/caseStatus", handle_route)

        print("Navigating to PERM status page...")
        await page.goto(
            "https://flag.dol.gov/case-status-search",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await asyncio.sleep(3)

        print("Looking for case ID input...")

        try:
            case_input = await page.wait_for_selector("#cases-textarea", timeout=10000)
            await case_input.click()
            await asyncio.sleep(0.5)
            await case_input.type(CASE_ID, delay=100)
            await asyncio.sleep(1)
        except Exception as e:
            print("Could not find case input: " + str(e))

        await page.evaluate("() => { window.scrollBy(0, 200); }")
        await asyncio.sleep(1)

        print("Clicking search button...")

        try:
            search_button = await page.wait_for_selector(
                'button[type="submit"]', timeout=10000
            )
            await search_button.click()
        except Exception as e:
            print("Could not find search button: " + str(e))

        max_wait = 120
        waited = 0
        last_log = 0

        print("Waiting for reCAPTCHA to solve (may take up to 120 seconds)...")

        while waited < max_wait:
            # Check if we got the API response
            if api_response:
                print("Got case status response!")
                await browser.close()
                return api_response

            if waited - last_log >= 10:
                print("   Still waiting... (" + str(waited) + "s)")
                last_log = waited

            await asyncio.sleep(1)
            waited += 1

        print("Timed out after 120 seconds")
        await browser.close()
        return None


def send_pushover_notification(title, message, priority=0):
    print("Sending Pushover notification: " + title)
    try:
        api = PushoverAPI(token=PUSHOVER_API_TOKEN)
        api.send_message(PUSHOVER_USER_KEY, message, title=title, priority=priority)
        print("Notification sent: " + title)
    except PushoverCompleteError as e:
        print("Error sending Pushover notification: " + str(e))


def check_required_env_vars():
    missing = []

    if not PUSHOVER_USER_KEY or PUSHOVER_USER_KEY == "your_pushover_user_key_here":
        missing.append("PUSHOVER_USER_KEY")
    if not PUSHOVER_API_TOKEN or PUSHOVER_API_TOKEN == "your_pushover_api_token_here":
        missing.append("PUSHOVER_API_TOKEN")

    if missing:
        print("Missing required environment variables:")
        for var in missing:
            print("   - " + var)
        print()
        print("Please set them in your .env file before running.")
        print()
        print("Example:")
        print("  PUSHOVER_USER_KEY=your_key")
        print("  PUSHOVER_API_TOKEN=your_token")
        return False

    return True


async def main():
    if not check_required_env_vars():
        sys.exit(1)

    print("Checking case status for: " + CASE_ID)
    tz = os.getenv("TZ", "UTC")
    print("Timezone: " + tz)
    print("-" * 50)

    try:
        result = await get_case_status()

        if not result:
            send_pushover_notification(
                "PERM Check Error",
                "Failed to get case status",
                priority=1,
            )
            sys.exit(1)

        print("Case status: " + json.dumps(result, indent=2))

        if isinstance(result, dict) and "value" in result:
            cases = result["value"]
            if isinstance(cases, list) and len(cases) > 0:
                case_data = cases[0]
                case_number = case_data.get("caseNumber", "Unknown")
                status = case_data.get("caseStatus", "Unknown")
                visa_type = case_data.get("visaType", "Unknown")
                employer = case_data.get("employerName", "Unknown")
                job_title = case_data.get("jobTitle", "Unknown")
                submitted = case_data.get("submittedDate", "Unknown")

                title = "PERM Case Update: " + case_number
                message = f"""
Status: {status}
Employer: {employer}
Job Title: {job_title}
Visa Type: {visa_type}
Case Number: {case_number}
Submitted: {submitted}
                    """

                send_pushover_notification(title, message)
            else:
                send_pushover_notification(
                    "PERM Case Check: " + CASE_ID, "No case data found"
                )
        else:
            send_pushover_notification("PERM Case Check: " + CASE_ID, str(result))

    except Exception as e:
        error_msg = "Error: " + str(e)
        print(error_msg)
        send_pushover_notification(
            "PERM Check Error",
            error_msg,
            priority=1,
        )


if __name__ == "__main__":
    asyncio.run(main())

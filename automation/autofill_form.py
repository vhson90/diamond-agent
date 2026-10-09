"""
Playwright CDP Autofill: Populates Claude for Startups Application with DiamondAgent data.
Connects to local Chrome browser running on port 9222.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

STARTUP_PROFILE = {
    "company_name": "Hanh Trinh Diamond",
    "project_name": "DiamondAgent",
    "website": "https://hanhtrinhdiamond.com",
    "company_email": "contact@hanhtrinhdiamond.com",
    "founding_year": "2024",
    "funding_stage": "Bootstrapped / Pre-seed",
    "team_size": "2-10",
    "product_pitch": (
        "DiamondAgent is an enterprise-grade autonomous multi-agent orchestration and knowledge graph engine "
        "built natively on Claude 3.5 Sonnet and the Model Context Protocol (MCP). We eliminate fragile single-prompt "
        "LLM chains through a self-correcting Planner-Worker-Critic network, utilizing Anthropic's ephemeral prompt "
        "caching to achieve up to 85% token latency reduction and sandboxed MCP tool execution."
    ),
    "claude_use_case": (
        "We utilize Claude 3.5 Sonnet for high-reasoning planning and code execution tasks, Claude 3.5 Haiku "
        "for low-latency worker agents, and Claude 3 Opus for complex quality review gates. The product integrates "
        "MCP servers for sandboxed enterprise filesystem and database operations."
    ),
    "github_url": "https://github.com/vhson90/diamond-agent",
}


async def autofill_startup_form():
    print(f"[*] Connecting to Chrome on http://127.0.0.1:9222...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        except Exception as e:
            print(f"[!] Cannot connect to Chrome: {e}")
            return

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"[*] Active page URL: {page.url}")
        if "startups-application" not in page.url:
            print("[*] Navigating to startups application page...")
            await page.goto("https://platform.claude.com/offers/startups-application", wait_until="networkidle")

        print("[*] Autofilling fields based on keywords...")
        filled_count = await page.evaluate(f"""
            (data) => {{
                let count = 0;
                const inputs = Array.from(document.querySelectorAll('input, textarea'));
                inputs.forEach(el => {{
                    const labelText = (el.closest('label')?.innerText || el.placeholder || el.name || el.id || '').toLowerCase();
                    
                    if (labelText.includes('company') || labelText.includes('startup') || labelText.includes('legal name')) {{
                        el.value = data.company_name;
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        count++;
                    }} else if (labelText.includes('website') || labelText.includes('url') || labelText.includes('domain')) {{
                        el.value = data.website;
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        count++;
                    }} else if (labelText.includes('email')) {{
                        el.value = data.company_email;
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        count++;
                    }} else if (labelText.includes('building') || labelText.includes('description') || labelText.includes('pitch') || labelText.includes('about')) {{
                        el.value = data.product_pitch;
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        count++;
                    }} else if (labelText.includes('claude') || labelText.includes('use case') || labelText.includes('integrate')) {{
                        el.value = data.claude_use_case;
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        count++;
                    }}
                }});
                return count;
            }}
        """, STARTUP_PROFILE)

        print(f"[+] Autofilled {filled_count} fields matching profile.")
        print("[!] Please check your Chrome window to review the form.")


if __name__ == "__main__":
    asyncio.run(autofill_startup_form())

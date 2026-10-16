#!/usr/bin/env python3
"""
Test the stepper in a headless browser using Playwright.
Verify:
- No console errors
- graph-svg has >26 child elements
- tree-canvas has non-blank pixels
- Caption changes when clicking next
- Mobile viewport works
"""

import sys
import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Installing playwright...")
    os.system("pip install playwright")
    os.system("playwright install chromium")
    from playwright.sync_api import sync_playwright

def test_stepper():
    """Test the stepper in browser"""
    artifacts_dir = Path("/opt/cursor/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    html_path = Path("/workspace/docs/hk-explained/index.html").resolve()
    if not html_path.exists():
        print(f"ERROR: {html_path} not found")
        return False
    
    print(f"Testing: {html_path}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # Desktop test
        print("\n=== Desktop test (1920x1080) ===")
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        errors = []
        page.on("console", lambda msg: print(f"Console [{msg.type}]: {msg.text}") if msg.type in ["error", "warning"] else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(2000)  # Wait for init
        
        # Check for JS errors
        if errors:
            print(f"✗ FAIL: {len(errors)} JavaScript errors:")
            for err in errors:
                print(f"  - {err}")
            return False
        print("✓ No console errors")
        
        # Scroll to stepper section
        page.evaluate("document.querySelector('#stepper').scrollIntoView()")
        page.wait_for_timeout(500)
        
        # Check graph-svg has children
        graph_children = page.locator("#graph-svg > *").count()
        print(f"graph-svg children: {graph_children}")
        if graph_children < 26:
            print(f"✗ FAIL: graph-svg has only {graph_children} children (expected >26)")
            return False
        print(f"✓ graph-svg has {graph_children} child elements")
        
        # Check tree-canvas is not blank
        canvas_data = page.evaluate("""
            () => {
                const canvas = document.getElementById('tree-canvas');
                if (!canvas) return null;
                const ctx = canvas.getContext('2d');
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const pixels = imageData.data;
                let nonWhite = 0;
                for (let i = 0; i < pixels.length; i += 4) {
                    if (pixels[i] !== 255 || pixels[i+1] !== 255 || pixels[i+2] !== 255) {
                        nonWhite++;
                    }
                }
                return nonWhite;
            }
        """)
        
        if canvas_data is None or canvas_data == 0:
            print("✗ FAIL: tree-canvas is blank")
            return False
        print(f"✓ tree-canvas has {canvas_data} non-white pixels")
        
        # Get initial caption
        initial_caption = page.locator("#caption").inner_text()
        print(f"Initial caption: {initial_caption[:50]}...")
        
        # Screenshot initial state
        page.screenshot(path=str(artifacts_dir / "stepper_desktop_initial.png"), full_page=False)
        print(f"✓ Saved screenshot: {artifacts_dir}/stepper_desktop_initial.png")
        
        # Click next button several times
        for i in range(3):
            page.click("#btn-next")
            page.wait_for_timeout(500)
        
        # Check caption changed
        new_caption = page.locator("#caption").inner_text()
        print(f"After 3 steps caption: {new_caption[:50]}...")
        
        if initial_caption == new_caption:
            print("✗ FAIL: Caption did not change after clicking next")
            return False
        print("✓ Caption changes when clicking next")
        
        # Screenshot after steps
        page.screenshot(path=str(artifacts_dir / "stepper_desktop_after_steps.png"), full_page=False)
        print(f"✓ Saved screenshot: {artifacts_dir}/stepper_desktop_after_steps.png")
        
        page.close()
        
        # Mobile test
        print("\n=== Mobile test (390x844) ===")
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        
        mobile_errors = []
        mobile_page.on("pageerror", lambda exc: mobile_errors.append(str(exc)))
        
        mobile_page.goto(f"file://{html_path}")
        mobile_page.wait_for_timeout(2000)
        
        if mobile_errors:
            print(f"✗ FAIL: {len(mobile_errors)} JavaScript errors on mobile")
            return False
        print("✓ No console errors on mobile")
        
        # Scroll to stepper
        mobile_page.evaluate("document.querySelector('#stepper').scrollIntoView()")
        mobile_page.wait_for_timeout(500)
        
        # Check graph exists
        mobile_graph_children = mobile_page.locator("#graph-svg > *").count()
        if mobile_graph_children < 26:
            print(f"✗ FAIL: Mobile graph-svg has only {mobile_graph_children} children")
            return False
        print(f"✓ Mobile graph-svg has {mobile_graph_children} child elements")
        
        # Screenshot mobile initial
        mobile_page.screenshot(path=str(artifacts_dir / "stepper_mobile_initial.png"), full_page=False)
        print(f"✓ Saved screenshot: {artifacts_dir}/stepper_mobile_initial.png")
        
        # Click next on mobile
        mobile_page.click("#btn-next")
        mobile_page.wait_for_timeout(500)
        
        mobile_page.screenshot(path=str(artifacts_dir / "stepper_mobile_after_step.png"), full_page=False)
        print(f"✓ Saved screenshot: {artifacts_dir}/stepper_mobile_after_step.png")
        
        mobile_page.close()
        browser.close()
        
        return True

if __name__ == '__main__':
    print("Testing stepper in headless browser...")
    success = test_stepper()
    
    if success:
        print("\n=== ALL BROWSER TESTS PASSED ===")
        sys.exit(0)
    else:
        print("\n=== BROWSER TESTS FAILED ===")
        sys.exit(1)

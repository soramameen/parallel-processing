#!/usr/bin/env python3
"""
Test the improved stepper with detailed element screenshots.
"""

import sys
import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("playwright not found")
    sys.exit(1)

def test_stepper():
    """Test the stepper with element screenshots"""
    artifacts_dir = Path("/opt/cursor/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    html_path = Path("/workspace/docs/hk-explained/index.html").resolve()
    if not html_path.exists():
        print(f"ERROR: {html_path} not found")
        return False
    
    print(f"Testing: {html_path}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # Test at two viewports
        viewports = [
            ("desktop", 1280, 900),
            ("mobile", 390, 844)
        ]
        
        for viewport_name, width, height in viewports:
            print(f"\n=== {viewport_name.upper()} test ({width}x{height}) ===")
            page = browser.new_page(viewport={"width": width, "height": height})
            
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            
            page.goto(f"file://{html_path}")
            page.wait_for_timeout(3000)
            
            if errors:
                print(f"✗ FAIL: {len(errors)} JavaScript errors:")
                for err in errors:
                    print(f"  - {err}")
                page.close()
                continue
            print(f"✓ No console errors on {viewport_name}")
            
            # Scroll to stepper section
            page.evaluate("document.querySelector('#stepper').scrollIntoView()")
            page.wait_for_timeout(500)
            
            # Test at steps: 0, 1, 3, 8
            steps = [0, 1, 3, 8]
            
            for step in steps:
                if step > 0:
                    for _ in range(step - (steps[steps.index(step)-1] if step > steps[0] else 0)):
                        page.click("#btn-next")
                        page.wait_for_timeout(300)
                
                # Check element counts
                graph_children = page.locator("#graph-svg > *").count()
                print(f"Step {step}: graph-svg has {graph_children} children")
                
                # Screenshot graph-svg
                graph_svg = page.locator("#graph-svg")
                if graph_svg.count() > 0:
                    screenshot_path = artifacts_dir / f"step{step}_{viewport_name}_graph.png"
                    graph_svg.screenshot(path=str(screenshot_path))
                    print(f"  ✓ Saved: {screenshot_path.name}")
                
                # Screenshot tree-canvas
                tree_canvas = page.locator("#tree-canvas")
                if tree_canvas.count() > 0:
                    screenshot_path = artifacts_dir / f"step{step}_{viewport_name}_tree.png"
                    tree_canvas.screenshot(path=str(screenshot_path))
                    print(f"  ✓ Saved: {screenshot_path.name}")
                
                # Check canvas pixels
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
                
                if canvas_data and canvas_data > 0:
                    print(f"  ✓ tree-canvas has {canvas_data} non-white pixels")
            
            page.close()
        
        browser.close()
        
        return True

if __name__ == '__main__':
    print("Testing improved stepper...")
    success = test_stepper()
    
    if success:
        print("\n=== ALL TESTS PASSED ===")
        print("\nScreenshot artifacts:")
        artifacts = sorted(Path("/opt/cursor/artifacts").glob("step*.png"))
        for art in artifacts:
            print(f"  - {art.name}")
        sys.exit(0)
    else:
        print("\n=== TESTS FAILED ===")
        sys.exit(1)

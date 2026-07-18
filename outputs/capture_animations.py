import os
import sys
import time
import subprocess
from pathlib import Path

# Ensure dependencies are installed
try:
    import playwright
except ImportError:
    print("Installing Playwright...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    import playwright

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

from playwright.sync_api import sync_playwright

workspace_root = Path(r"c:\Users\Zhane\Documents\New project\zrt-bionemo")
output_dir = workspace_root  # Save directly to the root folder

def capture_protein(name, option_val, rep_style, duration_seconds=6):
    file_prefix = f"{name}_{rep_style}"
    print(f"\nCapturing screenshots and animation for: {file_prefix}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Set large viewport for premium visuals
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        
        # Open local viewer
        url = "http://127.0.0.1:8085/outputs/viewer.html"
        print(f"Navigating to {url}...")
        page.goto(url)
        
        # Allow initial rendering
        time.sleep(3)
        
        # Select target protein in dropdown
        print(f"Selecting protein: {option_val}...")
        page.select_option("#proteinSelect", value=option_val)
        time.sleep(2)
        
        # Select representation style
        print(f"Selecting representation: {rep_style}...")
        page.select_option("#repStyle", value=rep_style)
        time.sleep(3)  # Wait for structure styles to render
        
        # 1. Capture Static Screenshot
        screenshot_path = output_dir / f"{file_prefix}_viewer.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Saved static screenshot to {screenshot_path}")
        
        # 2. Toggle Spin and Capture Frames for GIF
        print("Toggling spin and capturing frames for GIF...")
        page.click("text=Toggle Spin")
        time.sleep(0.5) # Let it start spinning
        
        frames = []
        num_frames = 20
        delay = duration_seconds / num_frames
        
        for i in range(num_frames):
            frame_path = output_dir / f"temp_frame_{i}.png"
            page.screenshot(path=str(frame_path))
            frames.append(Image.open(frame_path))
            time.sleep(delay)
            
        # Compile frames to animated GIF
        gif_path = output_dir / f"{file_prefix}_viewer.gif"
        frames[0].save(
            str(gif_path),
            save_all=True,
            append_images=frames[1:],
            optimize=True,
            duration=int(delay * 1000),
            loop=0
        )
        print(f"Saved animated GIF to {gif_path}")
        
        # Clean up temporary frames
        for i in range(num_frames):
            frame_path = output_dir / f"temp_frame_{i}.png"
            if frame_path.exists():
                frame_path.unlink()
                
        browser.close()

if __name__ == "__main__":
    try:
        # Helical bundle options
        capture_protein("helical_bundle", "helical", "cartoon")
        capture_protein("helical_bundle", "helical", "sphere")
        
        # Mixed fold options
        capture_protein("mixed_fold", "mixed", "stick")
        capture_protein("mixed_fold", "mixed", "line")
        
        print("\nAll capturing completed successfully!")
    except Exception as e:
        print(f"Error during capturing: {e}")
        sys.exit(1)

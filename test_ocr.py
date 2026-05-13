"""
TEST_OCR.py - Test License Plate OCR on Sample Images
================================================================

RUN: python test_ocr.py

Used to test OCR on image files in the captures/ directory or any local image.
"""

import os
import sys
import cv2
from typing import Tuple

from lpr import read_plate_from_image, read_plate_from_frame, normalize_plate

def test_image(image_path: str) -> Tuple[str, float]:
    """Test OCR on a single image."""
    if not os.path.exists(image_path):
        print(f"  ❌ Image not found: {image_path}")
        return "", 0.0
    
    print(f"\n  📸 Testing: {image_path}")
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"  ❌ Could not read image")
            return "", 0.0
        
        plate, conf = read_plate_from_image(image_path)
        plate_norm = normalize_plate(plate)
        
        print(f"     Raw OCR      : {plate}")
        print(f"     Normalized   : {plate_norm}")
        print(f"     Confidence   : {conf:.1%}")
        
        if plate_norm:
            print(f"     ✅ Valid plate detected")
        else:
            print(f"     ⚠️ No valid plate detected")
        
        return plate_norm, conf
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return "", 0.0


def test_directory(dir_path: str = "captures", extensions: tuple = (".jpg", ".png", ".bmp")):
    """Test OCR on all images in a directory."""
    if not os.path.exists(dir_path):
        print(f"  ❌ Directory not found: {dir_path}")
        return
    
    print("\n" + "="*70)
    print(f"  🔍 Testing OCR on images in: {dir_path}")
    print("="*70)
    
    images = [f for f in os.listdir(dir_path) if f.lower().endswith(extensions)]
    
    if not images:
        print(f"  (No images found in {dir_path})")
        return
    
    results = []
    for img_file in sorted(images)[-10:]:  # Last 10 images
        img_path = os.path.join(dir_path, img_file)
        plate, conf = test_image(img_path)
        if plate:
            results.append((img_file, plate, conf))
    
    if results:
        print("\n" + "="*70)
        print("  📋 RESULTS SUMMARY")
        print("="*70)
        for img, plate, conf in results:
            print(f"  {img:<35} → {plate:<12} ({conf:.1%})")
        print("="*70)


def interactive_test():
    """Interactive OCR testing."""
    print("\n" + "="*70)
    print("  🅿️  INTERACTIVE OCR TESTER")
    print("="*70)
    print("  1. Test all captures/ directory images")
    print("  2. Test specific image file")
    print("  3. Exit")
    print("="*70)
    
    choice = input("  Select option (1-3): ").strip()
    
    if choice == "1":
        test_directory("captures")
    elif choice == "2":
        image_path = input("  Enter image path: ").strip()
        test_image(image_path)
    elif choice == "3":
        print("\n  👋 Goodbye!\n")
    else:
        print("  ❌ Invalid option")


def main():
    """Main entry point."""
    # Test if captures directory has images
    if os.path.exists("captures") and os.listdir("captures"):
        test_directory("captures")
    else:
        print("\n  ℹ️  No captures/ directory or empty. Running interactive mode...\n")
        interactive_test()


if __name__ == "__main__":
    main()

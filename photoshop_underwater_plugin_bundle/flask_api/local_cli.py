import argparse
import os

from main import process_image


def main():
    parser = argparse.ArgumentParser(description="Run underwater correction locally")
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("output_path", help="Path for the corrected output image")
    parser.add_argument("--advanced", action="store_true", help="Use advanced Sea-Thru")
    args = parser.parse_args()

    if args.advanced:
        os.environ["ADVANCED_SEATHRU"] = "1"

    result = process_image(image_path=args.image_path, output_path=args.output_path)
    print(f"Saved corrected image to {args.output_path}")
    print(result["adjustments"])


if __name__ == "__main__":
    main()

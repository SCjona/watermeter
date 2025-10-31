import argparse
import os
import sys


def do_init(args):
    from image_processor import get_ocr
    get_ocr()
    print("OK")

def do_run(args):
    from image_processor import ImageProcessor
    ip = ImageProcessor(args.image, args.config)
    result = ip.process(debug=args.debug)

    max_threshold = None
    if "sanity" in ip.config:
        if "maxThreshold" in ip.config["sanity"]:
            max_threshold = ip.config["sanity"]["maxThreshold"]

    if result is None:
        print("Could not parse image")
        sys.exit(1)

    previous = None
    if os.path.exists(args.value):
        with open(args.value, "r") as f:
            previous = float(f.read())
    if previous is not None:
        if result < previous:
            print(f"Result {result} is less than previous {previous}")
            sys.exit(1)
        elif result > previous + 0.2:
            print(f"Result {result} exceeds previous + {max_threshold} ({previous + max_threshold})")
            sys.exit(1)

    with open(args.value, "w") as f:
        f.write(str(result))
    print(f"Result: {result}")


def main():
    parser = argparse.ArgumentParser(
        description="Process an image and extract digits using ImageProcessor with sanity checking."
    )

    subparsers = parser.add_subparsers(title="actions", dest="command", required=True, description="Action to perform")

    action_init = subparsers.add_parser("init", help="Performs initial setup (downloading detection model)")
    action_init.set_defaults(func=do_init)

    action_run = subparsers.add_parser("run", help="Perform a once-off operation")
    action_run.add_argument("-i", "--image", required=True, help="Path to input image")
    action_run.add_argument("-c", "--config", required=True, help="Path to JSON config file")
    action_run.add_argument("-v", "--value", required=True, help="Path to (last) value file")
    action_run.add_argument("-d", "--debug", required=False, type=bool, default=False, help="Save debugging image to help diagnose issues")
    action_run.set_defaults(func=do_run)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

import math

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw
import json
import easyocr

ocr = None

def get_ocr():
    global ocr
    if ocr is None:
        ocr = easyocr.Reader(["en"], gpu=False)
    return ocr

class ImageProcessor:
    def __init__(self, image_path: str, config_path: str):
        self.image_path = image_path
        self.config_path = config_path
        self.img = cv2.imread(image_path)
        with open(config_path, "r") as config_file:
            self.config = json.load(config_file)
        if self.img is None:
            raise ValueError("Image not found")

    def process(self, previous_value: None | float = None, debug: str | None = None) -> float:
        # Rotate the image
        (h, w) = self.img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), self.config["image"]["rotate"], 1.0)
        rotated = cv2.warpAffine(self.img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        #self.__debug_show_image("rotated", rotated)

        # Crop region of interest
        crop_cfg = self.config["image"]["crop"]
        x, y, cw, ch = crop_cfg["x"], crop_cfg["y"], crop_cfg["width"], crop_cfg["height"]
        cropped = rotated[y:y + ch, x:x + cw]
        #self.__debug_show_image("cropped", cropped)

        # Draw image for debugging
        debug_image = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(debug_image)

        # Extract digits
        # error handling so debug image still gets created
        err = None
        try:
            digits = self._parse_digits(cropped, draw, self.config["digits"])
        except Exception as e:
            if err is None:
                err = e
        try:
            decimal_digits = self._parse_digits(cropped, draw, self.config["decimal_digits"])
        except Exception as e:
            if err is None:
                err = e
        if decimal_digits is None:
            try:
                decimal_digits = self._parse_analogs(cropped, draw, self.config["decimal_analogs"])
            except Exception as e:
                if err is None:
                    err = e

        if debug is not None:
            # Save the combined output
            #self.__debug_show_image("digits", combined)
            #self.__debug_show_image("debug", debug_image)
            debug_image.save(debug)
            print("Debug image saved to " + debug)

        if err:
            raise err

        final_value = float(digits.replace("?", "0")) # if last digit parsing fails replace with 0
        if decimal_digits:
            decimal_value = float("0." + decimal_digits)
            if previous_value:
                # context aware parsing, last digit of the integer value may be wrong due to rotating nature
                # check if we're in range of it being inaccurate
                if decimal_value > 0.2:
                    final_value = math.floor(final_value / 10) * 10 # remove final digit
                    final_value += math.floor(previous_value) % 10 # add final digit of previous value
            final_value += decimal_value

        return final_value

    def _parse_digits(self, image, draw: ImageDraw.ImageDraw, digit_config: list[dict]):
        if len(digit_config) == 0:
            return None

        final_text = ""
        for d in digit_config:
            is_last_digit = d == digit_config[-1]
            dx, dy, dw, dh = d["x"], d["y"], d["width"], d["height"]
            digit_img = image[dy:dy + dh, dx:dx + dw]

            # Convert to PIL for brightness/contrast postprocessing
            digit_pil = Image.fromarray(cv2.cvtColor(digit_img, cv2.COLOR_BGR2RGB))

            # Apply brightness / contrast adjustments
            brightness = self.config["postprocessing"]["digits"]["brightness"]
            contrast = self.config["postprocessing"]["digits"]["contrast"]
            if brightness != 0:
                digit_pil = ImageEnhance.Brightness(digit_pil).enhance(1 + brightness / 100)
            if contrast != 0:
                digit_pil = ImageEnhance.Contrast(digit_pil).enhance(1 + contrast / 100)

            draw.rectangle((dx, dy, dx + dw - 1, dy + dh - 1), outline=(255, 0, 0), width=1)
            #self.__debug_show_image("digit", digit_pil)
            text = get_ocr().readtext(cv2.cvtColor(np.array(digit_pil), cv2.COLOR_RGB2BGR), allowlist="0123456789")
            if len(text) != 1:
                if is_last_digit:
                    final_text += "?"
                    continue
                raise ValueError("OCR failed #1")
            confidence = text[0][2]
            text = text[0][1]
            if len(text) != 1:
                if is_last_digit:
                    final_text += "?"
                    continue
                raise ValueError("OCR failed #2")
            final_text += text

        return final_text

    def _parse_analogs(self, image, draw: ImageDraw.ImageDraw, analogs_config: list[dict]) -> str | None:
        if len(analogs_config) == 0:
            return None
        result = []
        for analog in analogs_config:
            result.append(self._parse_analog(image, draw, analog))
        result_str = ""
        # perform context aware parsing
        # this helps with slightly off values due to perspective errors
        for i in range(len(result)):
            if i == len(result) - 1:
                result_str += str(math.floor(result[i]))
                break

            this_value = result[i]
            next_value = result[i + 1]
            if this_value % 1 > 0.9 and next_value < 1:
                this_value += 0.1
            elif this_value % 1 < 0.1 and next_value > 9:
                this_value -= 0.1
            result_str += str(math.floor(this_value))

        return result_str

    def _parse_analog(self, image, draw: ImageDraw.ImageDraw, cfg: dict):
        dx, dy, dw, dh, color = cfg["x"], cfg["y"], cfg["width"], cfg["height"], cfg["color"]
        draw.rectangle((dx, dy, dx + dw - 1, dy + dh - 1), outline=(255, 0, 0), width=1)
        draw.line((dx, dy, dx + dw - 1, dy + dh - 1), fill=(255, 0, 0), width=1)
        draw.line((dx, dy + dh - 1, dx + dw - 1, dy), fill=(255, 0, 0), width=1)

        analog_image = image[dy:dy + dh, dx:dx + dw]

        # Convert to PIL for brightness/contrast postprocessing
        analog_pil = Image.fromarray(cv2.cvtColor(analog_image, cv2.COLOR_BGR2RGB))

        # Apply brightness / contrast adjustments
        brightness = self.config["postprocessing"]["analog"]["brightness"]
        contrast = self.config["postprocessing"]["analog"]["contrast"]
        if brightness != 0:
            analog_pil = ImageEnhance.Brightness(analog_pil).enhance(1 + brightness / 100)
        if contrast != 0:
            analog_pil = ImageEnhance.Contrast(analog_pil).enhance(1 + contrast / 100)

        analog_image = cv2.cvtColor(np.array(analog_pil), cv2.COLOR_RGB2BGR)

        # white/gray to black, isolate colors
        color_index = -1
        if color == "red":
            color_index = 2
        elif color == "green":
            color_index = 1
        elif color == "blue":
            color_index = 0
        min_vals = np.min(analog_image, axis=2, keepdims=True)
        analog_image -= min_vals
        target_color_image = analog_image[:, :, color_index]
        _, target_color_image = cv2.threshold(target_color_image, self.config["postprocessing"]["analog"]["binaryThreshold"], 255, cv2.THRESH_BINARY)
        #self.__debug_show_image("analog", target_color_image)

        # now we need to find the white pixel furthest from the center
        height, width = target_color_image.shape
        white_pixels = np.column_stack(np.where(target_color_image == 255))
        if len(white_pixels) == 0:
            raise ValueError("Color not found in image or binaryThreshold too high")
        cx, cy = width // 2, height // 2
        distances = np.sqrt((white_pixels[:, 1] - cx) ** 2 + (white_pixels[:, 0] - cy) ** 2)

        furthest_idx = np.argmax(distances)
        py, px = white_pixels[furthest_idx]
        pdx = px - cx
        pdy = cy - py
        angle = math.degrees(math.atan2(pdx, pdy)) % 360
        value = angle / 36.0

        draw.line((dx + cx, dy + cy, dx + px, dy + py), fill=(0, 255, 0), width=3)

        if value < 0 or value >= 10:
            raise ValueError("Invalid angle")
        return value

    @staticmethod
    def __debug_show_image(name, image):
        if type(image) == Image.Image:
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        cv2.imshow(name, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
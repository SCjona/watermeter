# 💧 WaterMeter (EasyOCR Edition)

A **water meter reader** inspired by https://github.com/nohn/watermeter that uses **EasyOCR** (instead of Tesseract) to recognize digits on analog water meters. EasyOCR offers improved accuracy and robustness for digit recognition.

This project processes an image of your water meter, crops and corrects it based on a configuration file, extracts the relevant digit and analog fields, and produces a reliable reading with built-in sanity checks.

---

## 🚀 Features

* 🧠 Uses **EasyOCR** for digit recognition (better than Tesseract for uneven lighting or low contrast).
* 🔍 Supports **cropping and rotation** of the image to isolate the meter area.
* ⚙️ Configurable for different meter layouts via a JSON config file.
* 🧮 Includes **sanity checking**: ensures readings are consistent and realistic.
* 🐳 Easily run anywhere via **Docker**, no Python setup required.

---

## 🔧 General setup

This tool is intended to run in a minutely cronjob. 

This cronjob should first download an image from your camera.

If you have an RTSP stream you can use ffmpeg to take a picture from it:
```sh
ffmpeg -rtsp_transport tcp -i "rtsp://RTSP_STREAM_URL" -frames:v 1 -update 1 -q:v 2 -y /output/path/for/image.png
```

Then the cron job should process the camera image with this tool. The resulting value file can be copied into a webroot for further processing.

---

## 🧩 Example Configuration

Create a file named `config.json` based off the [configration example in this repository](./config-example.json)

---

## ⚙️ Configuration Explained

| Section             | Key            | Description                                                                                                                                     |
| ------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **sanity**          | `maxThreshold` | Maximum allowed increase in readings between runs (e.g., `0.2` means next reading can’t jump by more than 0.2 m³). Prevents OCR mistakes.       |
| **image**           | `rotate`       | Rotates the image (in degrees) to align the meter horizontally.                                                                                 |
|                     | `crop`         | Defines the rectangular region containing the entire meter display. Coordinates are relative to the original image.                             |
| **digits**          | list           | Each entry defines the x/y coordinates and width/height of an individual digit field in the main counter.                                       |
| **decimal_digits**  | list           | Optional fields for fractional digits (if present on your meter). Empty in this example.                                                        |
| **decimal_analogs** | list           | Circular or analog dials representing decimal fractions. Each field defines the area to analyze and its color channel (`red`, `green`, `blue`). |
| **postprocessing**  | `digits`       | Adjust brightness and contrast to improve OCR results for the main digits. Values are percentages (`-30` = darker, `40` = more contrast).       |
|                     | `analog`       | Same as above, but for analog (dial) sections. `binaryThreshold` defines the grayscale threshold used for detecting pointer position.           |

---

## 🐳 Run via Docker

Once you have your image and configuration ready, you can run the detector in one simple command:

```bash
docker run --rm -v $PWD:/app/data ghcr.io/SCjona/watermeter run \
  --image data/image.png \
  --config data/config.json \
  --value data/result.txt
```

---

## 🗂️ File Mappings Explained (for Docker Beginners)

Docker containers run in their own isolated filesystem.
The `-v $PWD:/app/data` flag **mounts** your current folder into the container.

So inside the container:

* `data/image.png` → your input photo of the meter
* `data/config.json` → your configuration file (like above)
* `data/result.txt` → output file containing the recognized reading

**Example:**
If you are running this command in `/home/user/watermeter/`, then this will be the file mapping:

```
/home/user/watermeter/image.png      # input image
/home/user/watermeter/config.json    # config
/home/user/watermeter/result.txt     # output created here
```

---

## 🧠 OCR Engine: EasyOCR

This version uses [**EasyOCR**](https://github.com/JaidedAI/EasyOCR), which is built on PyTorch and provides:

* Better character recognition under poor lighting
* Support for multiple fonts and rotated digits
* Fast and accurate performance on CPU (no CUDA required)

---

## 🧪 Development Setup (Optional)

If you prefer to run it locally (without Docker):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py run --image tests/0001.png --config tests/0001.json --value tests/0001.txt
```

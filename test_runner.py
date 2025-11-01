import unittest
from glob import glob
import os

from image_processor import ImageProcessor


class TestImagesInTests(unittest.TestCase):
    def test_all_images(self):
        images = glob("tests/*.png")
        self.assertGreater(len(images), 0)
        previous_value = None
        for image in images:
            image_id = os.path.basename(image)[:-4]
            image_path = os.path.join("tests", image_id + ".png")
            config_path = os.path.join("tests", image_id + ".json")
            result_path = os.path.join("tests", image_id + ".txt")
            ip = ImageProcessor(image_path, config_path)
            value = ip.process(previous_value)
            with open(result_path, "r") as result_file:
                result = float(result_file.read())
            self.assertEqual(result, value)
            previous_value = value


if __name__ == '__main__':
    unittest.main()

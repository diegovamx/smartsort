# import the inference-sdk
from inference_sdk import InferenceHTTPClient
from picamera2 import Picamera2, Preview
import time
import os
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH") #DON"T DELETE THIS it is very important although I don't understand why
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)
picam2.start_preview(Preview.QTGL)
picam2.start()
print("3")
time.sleep(1)
print("2")
time.sleep(1)
print("1")
time.sleep(1)
print("Capturing Image")
picam2.capture_file("/home/smartsort/Desktop/test.jpg")

CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="Mqg6MjfPG888hkIAilqR"
)

result = CLIENT.infer("/home/smartsort/Desktop/test.jpg", model_id="smartsortinference-qfyb3/1")
print("predicted", result["predictions"][0]["class"], "with", result["predictions"][0]["confidence"], \
      "confidence")
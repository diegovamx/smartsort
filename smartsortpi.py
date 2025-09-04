from inference import InferencePipeline
import cv2


pipeline = InferencePipeline(
   model_id="smartsortinference-qfyb3/1",      # Replace with your actual project ID and version (e.g., "smartsortinference-qfyb3/1")
   api_key="Mqg6MjfPG888hkIAilqR",                 # Your Roboflow API key
   # The 'device' argument will default to 'cpu' on Raspberry Pi
)


cap = cv2.VideoCapture(0)
while True:
   ret, frame = cap.read()
   if not ret:
       print("Camera error")
       break


   # Run inference
   result = pipeline.infer(frame, confidence=0.5)
   print(result)


   # Draw bounding boxes (optional)
   pred_img = pipeline.overlay(frame, result)
   cv2.imshow('Result', pred_img)
   if cv2.waitKey(1) == 27:
       break


cap.release()
cv2.destroyAllWindows()
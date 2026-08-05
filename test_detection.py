from ultralytics import YOLO
import cv2
import time

# Modell laden (lädt beim ersten Mal automatisch yolov8n.pt herunter, ~6MB)
print("Lade YOLOv8n Modell...")
model = YOLO("yolov8n.pt")

# Testbild laden
img_path = "test.jpg"

# Inferenz mit Zeitmessung (wichtig fürs FPS-Gefühl auf dem Pi)
start = time.time()
results = model(img_path, classes=[0])  # class 0 = person (COCO)
elapsed = time.time() - start

print(f"Inferenzzeit: {elapsed:.2f}s")

# Ergebnisse auswerten
result = results[0]
num_persons = len(result.boxes)
print(f"Erkannte Personen: {num_persons}")

for box in result.boxes:
    conf = float(box.conf[0])
    xyxy = box.xyxy[0].tolist()
    print(f"  -> Confidence: {conf:.2f}, Box: {[round(x) for x in xyxy]}")

# Annotiertes Bild speichern
annotated = result.plot()
cv2.imwrite("test_annotated.jpg", annotated)
print("Gespeichert: test_annotated.jpg")

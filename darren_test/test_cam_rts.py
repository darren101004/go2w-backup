import cv2

print("Opening RTSP stream...")
cap = cv2.VideoCapture("rtsp://100.86.234.90:8554/mystream")

if not cap.isOpened():
    print("Failed to open the RTSP stream.")
else:
    print("RTSP stream opened successfully.")

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from stream. Exiting loop.")
        break
    frame_count += 1
    print(f"Displaying frame #{frame_count}")
    cv2.imshow("RTSP", frame)
    key = cv2.waitKey(1)
    if key == 27:
        print("ESC key pressed. Exiting.")
        break
cap.release()
cv2.destroyAllWindows()
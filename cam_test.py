import cv2
cap = cv2.VideoCapture(0)
print("Camera open hua:", cap.isOpened())
ret, frame = cap.read()
print("Frame mili:", ret)
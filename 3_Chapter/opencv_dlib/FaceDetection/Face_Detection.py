import cv2


cascPath = "haarcascade_frontalface_alt.xml"
# cascPath = "lbpcascade_frontalface.xml"
# cascPath = "haarcascade_smile.xml"
faceCascade = cv2.CascadeClassifier(cascPath)

video_capture = cv2.VideoCapture(0)
video_capture.set(3, 1920)
video_capture.set(4, 1080)
SKIP_FRAMES = 3
dets = []
count = 0
face_fx = face_fy = 0.33
while True:
    # Capture frame-by-frame
    ret, frame = video_capture.read()



    # Draw a rectangle around the faces


    if count % SKIP_FRAMES == 0:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(frame, (0, 0), fx=face_fx, fy=face_fx)


        faces = faceCascade.detectMultiScale(
            small,
            scaleFactor=1.06,
            minNeighbors=8,
            # minSize=(30, 30),

            # flags=cv2.cv.CV_HAAR_SCALE_IMAGE
        )
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (int(x/face_fx), int(y/face_fy)), (int((x + w)/face_fx), int((y + h)/face_fy)), (0, 255, 0), 2)
    # Display the resulting frame
    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
video_capture.release()
cv2.destroyAllWindows()
import cv2
import dlib
detector = dlib.get_frontal_face_detector()

cascPath = "haarcascade_frontalface_alt.xml"
# cascPath = "lbpcascade_frontalface.xml"
# cascPath = "haarcascade_smile.xml"
faceCascade = cv2.CascadeClassifier(cascPath)

video_capture = cv2.VideoCapture(0)
video_capture1 = cv2.VideoCapture(1)
# video_capture.set(3, 640)
# video_capture.set(4, 480)
video_capture.set(3, 1280)
video_capture.set(4, 720)
font = cv2.FONT_HERSHEY_SIMPLEX
SKIP_FRAMES = 3
dets = []
count = 0
face_fx = face_fy = 0.33

while True:
    # Capture frame-by-frame
    ret, frame = video_capture.read()
    ret1, frame1 = video_capture1.read()
    cv2.imshow('Video2', frame1)


    # faces = faceCascade.detectMultiScale(
    #     gray,
    #     scaleFactor=1.06,
    #     minNeighbors=8,
    #     # minSize=(30, 30),
    #
    #     # flags=cv2.cv.CV_HAAR_SCALE_IMAGE
    # )

    # Draw a rectangle around the faces
    # for (x, y, w, h) in faces:
    if count % SKIP_FRAMES == 0:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(frame, (0, 0), fx=face_fx, fy=face_fx)
        dets = detector(small, 1)
    for i, d in enumerate(dets):
        cv2.rectangle(frame, (int(d.left()/face_fx), int(d.top()/face_fy)), (int(d.right()/face_fx), int(d.bottom()/face_fy)), (0, 255, 0), 2)


    # Display the resulting frame
    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
video_capture.release()
cv2.destroyAllWindows()
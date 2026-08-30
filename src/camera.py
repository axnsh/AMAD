import cv2
import pygame

def capture_player_face(player_name, diameter):
    """Opens webcam and crops player face into a circular Pygame Surface."""
    cap = cv2.VideoCapture(0)

    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
    except Exception:
        face_cascade = None

    cropped_face_surface = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = []
        if face_cascade and not face_cascade.empty():
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        display_frame = frame.copy()
        cv2.putText(display_frame, f"{player_name}: Press SPACE to Snap Photo!", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Capture Player Face", display_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:  # Spacebar
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_img = frame[y:y+h, x:x+w]
            else:
                h_f, w_f, _ = frame.shape
                sz = min(h_f, w_f)
                cy, cx = h_f // 2, w_f // 2
                face_img = frame[cy - sz//2: cy + sz//2, cx - sz//2: cx + sz//2]

            face_img = cv2.resize(face_img, (diameter, diameter))
            face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

            raw_surface = pygame.image.frombuffer(face_rgb.tobytes(), (diameter, diameter), "RGB")

            mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (diameter // 2, diameter // 2), diameter // 2)

            cropped_face_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            cropped_face_surface.blit(raw_surface, (0, 0))
            cropped_face_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            break

    cap.release()
    cv2.destroyAllWindows()
    return cropped_face_surface
import cv2
import face_recognition as fr
import numpy as np


def get_Data():
    try:
        return list(np.load('email.npy')), list(np.load("balance.npy")), list(np.load('encoding.npy')), list(np.load('faces.npy'))
    except Exception as e:
        print(e)
        return list(), list(), list(), list()

MAILS, BALANCE, ENCODING, FACES = get_Data()


def register_on_submit(email, balance, encoding, face_image):
    try:
        path = 'static/' + email.split("@")[0] + "_1.jpg"
        cv2.imwrite(path, face_image)
        FACES.append(path)
        BALANCE.append(balance)
        ENCODING.append(list(encoding))
        MAILS.append(email)

        np.save('email.npy', MAILS) 
        np.save("balance.npy", BALANCE)
        np.save('encoding', ENCODING)
        np.save('faces.npy', FACES)
    except Exception as e:
        print(e)
        return "Registration failed!"
    return "Registration Successful!"

def match_on_login(email, encoding):
    try:
        # print(MAILS, BALANCE, ENCODING, FACES)
        index = MAILS.index(email)
        target_encoding = np.array(ENCODING[index])
        results = fr.compare_faces(encoding, target_encoding)
        if(results[0]):
            return {'res':"Successfully Logged in!", 'index': index}
        else:
            return {'res': "Failed to Recognize!"}
    except Exception as e:
        print(e)
        return {'res': "Failed to Recognize!"}
# face_image, encoding = get_face()
def login_check(email):
    if email in MAILS:
        return {'res':"Successfully Logged in!", 'index': MAILS.index(email)}
    else:
        return {'res': "Failed to Log in!"}
# print(face_image.shape)
# print(encoding)
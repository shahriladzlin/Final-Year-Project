from flask import Flask, render_template, request, url_for, redirect, Blueprint, send_from_directory, Response
from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired
import os
from face_utils import register_on_submit as rs
from face_utils import *
import time
from imutils.video import VideoStream


class Camera1:
    def __init__(self, cam_url):
        self.frame = None
        self.camera = cv2.VideoCapture(cam_url)#.start()
    
    def gen_frames(self):  # generate frame by frame from camera

        while True:
            _, self.frame = self.camera.read()
            if self.frame is not None:    
                try:
                    ret, buffer = cv2.imencode('.jpg', cv2.flip(self.frame,1))
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                except Exception as e:
                    pass
            else:
                pass

    def get_encoding(self):

        faces = fr.face_locations(self.frame)
        encoding = fr.face_encodings(self.frame, known_face_locations=faces)
        return encoding

cam = Camera1(cam_url = 1)

main = Blueprint('main', __name__)

secret_key = str(os.urandom(24))

app = Flask(__name__)
app.config['TESTING'] = True
app.config['DEBUG'] = False
app.config['FLASK_ENV'] = 'deployment'
app.config['SECRET_KEY'] = secret_key

app.register_blueprint(main)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    url = StringField('DataURL', validators=[])
    submit = SubmitField('LOGIN')


email = None
url = None
balance = 0

login_status = False
status = None
status1 = None

MAILS, BALANCE, ENCODING, FACES = get_Data()
Paid_Msg = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global email, url, login_status, status, cam
    MAILS, BALANCE, ENCODING, FACES = get_Data()
    form = LoginForm()
    Pay = 0
    Paid_Msg = None
# Login function using Login_form
    if request.method == "POST" and login_status:
        text = request.form['paid']
        Pay = int(text)
        time.sleep(2)
        encoding = cam.get_encoding()
        if not len(encoding):
            status1 = {'res': 'Face is not detected...'}
        else:
            status1 = match_on_login(email, encoding)
        if status1['res'] == "Successfully Logged in!":
            if BALANCE[status1['index']]>Pay:
                Paid_Msg = "$" + text + " Paid"
                try:
                    BALANCE[status1['index']] = BALANCE[status1['index']] - Pay
                    np.save('balance.npy', BALANCE)
                except:
                    pass
            else:
                Paid_Msg = "Your Balance is insufficient..."
        else:
            Paid_Msg = "Payment unsucessful, " + status1['res']
        print(text)

    if login_status:
        app.logger.info("Login Success")
        if Paid_Msg is None:
            Paid_Msg = status['res']
        try:
            index = status1['index']
        except:
            return render_template('success.html', msg=Paid_Msg, face_img = FACES[status['index']], name = MAILS[status['index']].split('@')[0], balance = BALANCE[status['index']])
        return render_template('success.html', msg=Paid_Msg, face_img = FACES[status1['index']], name = MAILS[status1['index']].split('@')[0], balance = BALANCE[status1['index']])
    
    if form.validate_on_submit():
        email = form.email.data
        url = form.url.data
        return redirect(url_for('.login'))
    elif request.method == 'POST':
        form.email.data = email
        form.url.data = url
    return render_template('index.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    global email, url, login_status, balance
    if login_status:
        app.logger.info("Login Success")
        return redirect(url_for('.login'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        url = form.url.data
        balance = request.form['balance']
        return redirect(url_for('.register_submit'))
    elif request.method == 'POST':
        form.email.data = email
        form.url.data = url
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global email, url, login_status, status, cam
    Paid_Msg = None
    if login_status:
        return redirect(url_for('.index'))


    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        url = form.url.data
        return redirect(url_for('.login'))
    elif request.method == 'POST':
        form.email.data = email
        form.url.data = url
    if email is None or email=='':
        return redirect(url_for('.index'))

    encoding = cam.get_encoding()
    if not len(encoding):
        status = {'res': 'Face is not detected...'}
    else:
        status = match_on_login(email, encoding)
    # status = login_check(email)
    print(status)
    if status['res'] == "Image not clear! Please try again!":
        return render_template('fail.html', msg=status['res'])
    if status['res'] == "Data does not exist!":
        return render_template('fail.html', msg=status['res'])
    if status['res'] == "Successfully Logged in!":
        app.logger.info("Login Success")
        login_status = True
        # return render_template('success.html', msg=status['res'], face_img = 'static/' + FACES[status['index']], name = MAILS[status['index']].split('@')[0], balance = BALANCE[status['index']])
        return redirect(url_for('.index'))
    else:
        app.logger.info("Login Fail")
        return render_template('fail.html', msg=status['res'])


@app.route('/register_submit')
def register_submit():
    global email, login_status, balance, status
    if email == '':
        return redirect(url_for('.register'))
    if email == None:
        return redirect(url_for('.register_submit'))

    print(balance)
    encoding = cam.get_encoding()
    # face_image, encoding = get_face()
    status = rs(email, int(balance), encoding, cam.frame)
    MAILS, BALANCE, ENCODING, FACES = get_Data()
    if status == "Registration Successful!":
        app.logger.info("Registration Success")
        login_status = False
        return redirect(url_for(".index"))
    else:
        app.logger.info("Registration fail")
        return render_template('fail.html', msg=status)

@app.route('/video_feed')
def video_feed():
    global cam
    return Response(cam.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logout')
def logout():
    global login_status
    login_status = False
    return redirect(url_for('.login'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run(debug=False)

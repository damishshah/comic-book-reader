import cv2
import base64
import io
import numpy
import os

from comic_book_reader import parseComicSpeechBubbles, segmentPage, findSpeechBubbles
from flask import Flask, Blueprint, jsonify, render_template, request, send_file

cbr = Blueprint('cbr', __name__,  url_prefix='/comic-book-reader')
application = Flask(__name__, static_url_path="/comic-book-reader/static", static_folder="static")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Traditionally production traffic would be better served by these static
#  files coming from nginx. For the purposes of our small app, this modular
#  approach of each app's resources being self contained is more convenient.
#
# We still use nginx at the host level to route traffic to different apps.
@cbr.route('/')
@cbr.route('/index')
def index():
    return render_template('index.html', title='Damish\'s ComicBookReader')

@cbr.route('/segment', methods=['POST'])
def segment():
    # Check if an image was sent with the POST request
    if 'image' not in request.files or not request.files['image']:
        return 'No file sent', 400

    file = request.files['image']
    
    if file and allowed_file(file.filename):
        npimg = numpy.fromstring(file.read(), numpy.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        contours = findSpeechBubbles(img)
        cv2.drawContours(img, contours, -1, (0, 255, 0), 3)
        _, buffer = cv2.imencode('.jpg', img)
        
        return send_file(
            io.BytesIO(buffer),
            mimetype='image/jpeg',
            as_attachment=True,
            attachment_filename='image.jpg')

@cbr.route('/read', methods=['POST'])
def read():
    # Check if an image was sent with the POST request
    if 'image' not in request.files or not request.files['image']:
        return 'No file sent', 400

    file = request.files['image']
    
    if file and allowed_file(file.filename):
        npimg = numpy.fromstring(file.read(), numpy.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        croppedImageList = segmentPage(img)
        pageText = parseComicSpeechBubbles(croppedImageList)
        data = {"pageText": pageText}
        return data, 200

application.register_blueprint(cbr)

if __name__ == '__main__':
     application.run()
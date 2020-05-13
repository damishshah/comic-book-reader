import cv2
import base64
import io
import numpy
import os

from comic_book_reader import parseComicSpeechBubbles, segmentPage, findSpeechBubbles
from flask import Flask, jsonify, render_template, request, send_file
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename

application = Flask(__name__, static_url_path="/comic-book-reader/static", static_folder="static")
api = Api(application)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Traditionally production traffic would be better served by these static
#  files coming from nginx. For the purposes of our small app, this modular
#  approach of each app's resources being self contained is more convenient.
#
# We still use nginx at the host level to route traffic to different apps.
@application.route('/')
@application.route('/index')
@application.route('/index/')
@application.route('/comic-book-reader')
@application.route('/comic-book-reader/')
def index():
    return render_template('index.html', title='Damish\'s ComicBookReader')

class SegmentPage(Resource):
    def post(self):
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

class ReadPage(Resource):
    def post(self):
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

api.add_resource(SegmentPage, '/segment')
api.add_resource(ReadPage, '/read')

if __name__ == '__main__':
     application.run()
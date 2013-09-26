import os, random, string
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug import secure_filename

from MakeGif import makegif

application = Flask(__name__)


#Set application.debug=true to enable tracebacks on Beanstalk log output. 
#Make sure to remove this line before deploying to production.
application.debug=True

UPLOAD_FOLDER = 'uploads/'
GIF_FOLDER = 'fz/'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def file_name_generator(legnth):
	return ''.join(random.sample(string.ascii_letters+string.digits,10))

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@application.route('/var')
def var():
	return str(os.getcwd())

@application.route('/fz/<filename>')
def uploaded_file(filename):
    return send_from_directory(GIF_FOLDER, filename)

@application.route('/layout/<name>')
def layout_files(name):
    return send_from_directory('layout/', name)

@application.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        upload_file = request.files['file']
        if upload_file and allowed_file(upload_file.filename):
            filename = file_name_generator(10) + '.' + upload_file.filename.rsplit('.', 1)[1].lower()
            upload_file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
            gif_file_name = makegif(os.path.join(application.config['UPLOAD_FOLDER'], filename), os.path.join((GIF_FOLDER + filename)))
            return redirect(GIF_FOLDER+gif_file_name[len(GIF_FOLDER):])
            #return redirect(url_for('fz', filename=gif_file_name[len(GIF_FOLDER):]))

        return 'File extention not allowed! only jpg or jpeg'

    return render_template('index.html')

if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True)
import os, random, string
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug import secure_filename

import boto

from MakeGif import makegif

application = Flask(__name__)
#sslify = SSLify(application) #adds https

#information to log onto s3 to save the image files
S3_PUBLIC_KEY = "AKIAIWHKKSAX2GVRHUZQ"
S3_PRIVATE_KEY = "mruUXSnyXU6ylrR3/ZAn66ND82YF4Vjkt/KSM5/W"

#setup for the connection to s3
s3_connection = boto.connect_s3(S3_PUBLIC_KEY, S3_PRIVATE_KEY)
fz_s3_bucket = s3_connection.get_bucket("fz-images")

#Set application.debug=true to enable tracebacks on Beanstalk log output. 
#Make sure to remove this line before deploying to production.
application.debug=False

#folders where uploads are temporary stored 
UPLOAD_FOLDER = 'uploads/'

#url used for images on the server
GIF_FOLDER = 'fz/'

#config for the uploads on the server
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png'])
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#generates 10 char file names made with upper lower case letters and numbers 0-9
def file_name_generator(legnth):
    return ''.join(random.sample(string.ascii_letters+string.digits,legnth))

#checks if a file name is allowed
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#/fz is deprecated and /im is what is used now.   this serves the web page with the image url stored in s3
@application.route('/fz/<imagename>')
@application.route('/im/<imagename>')
def uploaded_file(imagename):
    return render_template('image.html', imageurl="https://{0}.s3.amazonaws.com/{1}.gif".format(fz_s3_bucket.name, imagename), imagename=imagename)

#for the static content of the web-page
@application.route('/layout/<name>')
def layout_files(name):
    return send_from_directory('layout/', name)

#shows the content of the folders /fz and /uploads on the server.  used to test if any images have been forgotten to be deleted
@application.route('/test')
def test():
    import glob
    return str(glob.glob(os.getcwd()+"/fz/*")) + '\n' + str(glob.glob(os.getcwd()+"/uploads/*"))

#home page has both GET and POST options as the upload is against the root domain
@application.route('/', methods=['GET', 'POST'])
def upload_file():
    error = None
    if request.method == 'POST':
        upload_file = request.files['file']
        if upload_file and allowed_file(upload_file.filename):
            #save upload
            filename = file_name_generator(10) + '.' + upload_file.filename.rsplit('.', 1)[1].lower()
            filename_wpath = UPLOAD_FOLDER + filename
            upload_file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))

            #writes disk to disk
            gif_file_name_wpath = makegif(os.path.join(application.config['UPLOAD_FOLDER'], filename), os.path.join((GIF_FOLDER + filename)))

            #upload gif to s3
            s3_fz_key = boto.s3.key.Key(fz_s3_bucket)
            s3_fz_key.key = gif_file_name_wpath[len(GIF_FOLDER):]
            s3_fz_key.set_metadata("Content-Type", 'image/gif')
            s3_fz_key.set_contents_from_filename(GIF_FOLDER+gif_file_name_wpath[len(GIF_FOLDER):])
            s3_fz_key.make_public()

            #cleanup files
            os.remove(filename_wpath)
            os.remove(gif_file_name_wpath)

            return redirect('im/'+filename.rsplit('.', 1)[0])

        #error is used to store a string of the error.  Not rendered if blank.
        error = "File extension not allowed, use jpg, jpeg, png."
    return render_template('index.html', error=error)

#starts the web server, not sure if this is needed in production 
if __name__ == '__main__':
    application.run(host='0.0.0.0')
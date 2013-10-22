import os, random, string
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
from werkzeug import secure_filename
from fzdb import im_db
import hashlib, copy

import boto

from MakeGif import makegif

application = Flask(__name__)

#Set application.debug=true to enable tracebacks on Beanstalk log output. 
#Make sure to remove this line before deploying to production.
application.debug=False

#information to log onto s3 to save the image files
S3_PUBLIC_KEY = "AKIAIWHKKSAX2GVRHUZQ"
S3_PRIVATE_KEY = "mruUXSnyXU6ylrR3/ZAn66ND82YF4Vjkt/KSM5/W"

#setup for the connection to s3
s3_connection = boto.connect_s3(S3_PUBLIC_KEY, S3_PRIVATE_KEY)
fz_s3_bucket = s3_connection.get_bucket("fz-images")

#information to long onto db for images
db_PUBLIC_KEY = "AKIAIULWCPJA6GT3Y2WQ"
db_PRIVATE_KEY = "kWcj7xo55mm162VnXtm47E4MxNeZTNKo7JpIzrTX"

#connects to the db
fz_images_db = im_db(db_PUBLIC_KEY, db_PRIVATE_KEY)

#folders where uploads are temporary stored 
UPLOAD_FOLDER = 'uploads/'

#url used for images on the server
GIF_FOLDER = 'fz/'

#config for the uploads on the server
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png'])
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#to prevent double uploads
image_hashes = []

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

#simple api for latest zooms
@application.route('/api/latest/<int:number>')
@application.route('/api/latest/')
def get(number = 15):
    result = {}
    print(type(number))
    if number <= 100:
        try:
            images_dict = {}
            for item in fz_images_db.getimagenames(number):
                images_dict[item[0]] = item[1]
            result['IMAGES'] = images_dict
            status = "OK"
        except KeyError:
            status = "DB ERROR"
    else:
        status = "MAX results is 100"
    result["STATUS"] = status
    return jsonify(result)

#browse page
@application.route('/browse')
@application.route('/browse/')
@application.route('/browse/<int:pagenum>')
def browse(pagenum=0):
    images_url_list = []
    images_list = fz_images_db.getimagespage(pagenum)
    if not images_list:
        return render_template('browse.html', error= "No more images.")
    for item in fz_images_db.getimagespage(pagenum):
        #images_url_list.insert(0,"https://{0}.s3.amazonaws.com/{1}.gif".format(fz_s3_bucket.name, item[1]))
        images_url_list.insert(0, item[1])
    prevpage = None
    nextpage = pagenum + 1
    if pagenum != 0:
        prevpage = pagenum - 1
    return render_template('browse.html', images=images_url_list, prevpage=prevpage, nextpage=nextpage)

@application.route('/upload', methods=['POST', 'GET'])
def upload_file():
    error = None
    if request.method == 'POST':
        upload_file = request.files['file']
        if upload_file and allowed_file(upload_file.filename):
            #saves upload to disk
            filename = file_name_generator(10) + '.' + upload_file.filename.rsplit('.', 1)[1].lower()
            filename_wpath = UPLOAD_FOLDER + filename
            upload_file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))

            #checks upload unqunes, prevents back button from doing a duplicate upload
            sha1sum = hashlib.sha1(open(os.path.join(application.config['UPLOAD_FOLDER'], filename),'rb').read()).hexdigest()
            if sha1sum in image_hashes:
                #keeps the hash list short
                if len(image_hashes) > 25:
                    image_hashes.pop(0)
                #cleanup upload file
                os.remove(filename_wpath)
                return redirect('/upload')
            else:
                image_hashes.append(sha1sum)

            #writes gif to disk
            gif_file_name_wpath = makegif(os.path.join(application.config['UPLOAD_FOLDER'], filename), os.path.join((GIF_FOLDER + filename)))

            #compresses gif as much as possible: this isn't perfect so it it has been removed for now...
            #os.system("convert {0} -layers Optimize {0}".format(gif_file_name_wpath))

            #upload gif to s3
            s3_fz_key = boto.s3.key.Key(fz_s3_bucket)
            s3_fz_key.key = gif_file_name_wpath[len(GIF_FOLDER):]
            s3_fz_key.set_metadata("Content-Type", 'image/gif')
            s3_fz_key.set_contents_from_filename(GIF_FOLDER+gif_file_name_wpath[len(GIF_FOLDER):])
            s3_fz_key.make_public()

            #add to db
            fz_images_db.addimage(filename.rsplit('.', 1)[0])

            #cleanup files
            os.remove(filename_wpath)
            os.remove(gif_file_name_wpath)

            return redirect('im/'+filename.rsplit('.', 1)[0])

        #error is used to store a string of the error.  Not rendered if blank.
        error = "File extension not allowed, use jpg, jpeg, png."

    return render_template('index.html', error=error)


#home page has both GET and POST options as the upload is against the root domain
@application.route('/', methods=['GET'])
def index(error = None):
    return render_template('index.html', error=error)

#starts the web server, not sure if this is needed in production 
if __name__ == '__main__':
    application.run(host='0.0.0.0')
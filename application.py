import os, random, string
from flask import Flask, request, redirect, url_for, send_from_directory, render_template, jsonify
from werkzeug import secure_filename
from fzdb import im_db
import hashlib, copy
from StringIO import StringIO

#This is done so i can keep the source code on github safely
try:
    from aws_password import db_PUBLIC_KEY, db_PRIVATE_KEY, S3_PUBLIC_KEY, S3_PRIVATE_KEY
except:
    raise "This program intended to be deployed to AWS, and therefore requires access to an S3 filestore as well as Dynamo DB."

import boto

from MakeGif import makegif

application = Flask(__name__)

#Set application.debug=true to enable tracebacks on Beanstalk log output. 
#Make sure to remove this line before deploying to production.
application.debug=False

#setup for the connection to s3
s3_connection = boto.connect_s3(S3_PUBLIC_KEY, S3_PRIVATE_KEY)
fz_s3_bucket = s3_connection.get_bucket("fz-images")

#connects to the db
fz_images_db = im_db(db_PUBLIC_KEY, db_PRIVATE_KEY)

#folders where uploads are temporary stored 
UPLOAD_FOLDER = 'uploads/'

#config for the uploads on the server
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png'])
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#generates 10 char file names made with upper lower case letters and numbers 0-9
#does not check if filename is already used, and should't need too bc a name collision is so unlikely
def file_name_generator(legnth):
    return ''.join(random.sample(string.ascii_letters+string.digits,legnth))

#checks if a file name is allowed in uploaded files
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#/fz is deprecated and /im is what is used now.   this serves the web page with the image url stored in s3
#/fz is included here as to not break old links :)
@application.route('/fz/<imagename>')
@application.route('/im/<imagename>')
def uploaded_file(imagename):
    return render_template('image.html', imageurl="https://{0}.s3.amazonaws.com/{1}.gif".format(fz_s3_bucket.name, imagename), imagename=imagename)

#for the static content of the web-page
@application.route('/layout/<name>')
def layout_files(name):
    return send_from_directory('layout/', name)

#shows the content of the folders /fz and /uploads on the server.  used to test if any images have been forgotten to be deleted
#this is no longer needed as all file operations are now done using string streams in memory
@application.route('/test')
def test():
    import glob
    return str(glob.glob(os.getcwd()+"/fz/*")) + '\n' + str(glob.glob(os.getcwd()+"/uploads/*"))

#simple api for latest zooms, not used for anything...
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


@application.route('/api/1/upload', methods=['POST', 'GET'])
def upload_api():
    error = "Get not allowed."
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = file_name_generator(10) + '.' + uploaded_file.filename.rsplit('.', 1)[1].lower()
            if type(uploaded_file.stream) == file:
                uploaded_file_file = uploaded_file.stream
            else:
                uploaded_file_file = StringIO(uploaded_file.stream.getvalue())

            #generates gif and puts it in a stringio
            gif_stringio = makegif(uploaded_file_file)
            gif_stringio.seek(0)

            filename = file_name_generator(10) + '.gif'
            s3_fz_key = boto.s3.key.Key(fz_s3_bucket)
            s3_fz_key.key = filename
            s3_fz_key.set_metadata("Content-Type", 'image/gif')
            s3_fz_key.set_contents_from_file(gif_stringio)
            s3_fz_key.make_public()

            image_name = filename.rsplit('.', 1)[0]
            #add to db
            fz_images_db.addimage(image_name)

            result = {
                "image_id": image_name,
                "image_url": "https://{0}.s3.amazonaws.com/{1}.gif".format(fz_s3_bucket.name, image_name),
                "error": "NONE",
            }

            return jsonify(image_id=image_name,
                            image_url="https://{0}.s3.amazonaws.com/{1}.gif".format(fz_s3_bucket.name, image_name),
                            error="NONE")

        #error is used to store a string of the error.  Not rendered if blank.
        error = "File extension not allowed, use jpg, jpeg, png."

    return jsonify(error=error)


@application.route('/upload', methods=['POST', 'GET'])
def upload_file():
    error = None
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = file_name_generator(10) + '.' + uploaded_file.filename.rsplit('.', 1)[1].lower()
            
            #makes sure the upladed file is a certin type
            #flask is weird and changes the type based on filesize :/
            if type(uploaded_file.stream) == file:
                uploaded_file_file = uploaded_file.stream
            else:
                uploaded_file_file = StringIO(uploaded_file.stream.getvalue())

            #generates gif and puts it in a stringio
            gif_stringio = makegif(uploaded_file_file)
            gif_stringio.seek(0)

            #compresses gif as much as possible: this ruins the images so it it has been removed for now.
            #os.system("convert {0} -layers Optimize {0}".format(gif_file_name_wpath))

            filename = file_name_generator(10) + '.gif'
            s3_fz_key = boto.s3.key.Key(fz_s3_bucket)
            s3_fz_key.key = filename
            s3_fz_key.set_metadata("Content-Type", 'image/gif')
            s3_fz_key.set_contents_from_file(gif_stringio)
            s3_fz_key.make_public()

            #add to db
            fz_images_db.addimage(filename.rsplit('.', 1)[0])


            return redirect('im/'+filename.rsplit('.', 1)[0])

        #error is used to store a string of the error.  Not rendered if blank.
        error = "File extension not allowed, use jpg, jpeg, png."

    return render_template('index.html', error=error)


#home page
@application.route('/', methods=['GET'])
def index(error = None):
    return render_template('index.html', error=error)

#starts the web server, not sure if this is needed in production 
if __name__ == '__main__':
    application.run(host='0.0.0.0')

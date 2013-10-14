import boto
from fzdb import im_db

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

def remove_latest_zoom():
	name = fz_images_db.getimagenames(1)[0][1]+".gif"
	fz_s3_bucket.delete_key(name)
	fz_images_db.removelatest()

remove_latest_zoom()
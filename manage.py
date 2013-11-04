from fzdb import im_db
import boto
import os

#This is done so i keep the source code on github safely
try:
    from aws_password import db_PUBLIC_KEY, db_PRIVATE_KEY, S3_PUBLIC_KEY, S3_PRIVATE_KEY
except:
    raise "This program intended to be deployed to AWS, and therefore requires access to an S3 filestore as well as Dynamo DB."

#setup for the connection to s3
s3_connection = boto.connect_s3(S3_PUBLIC_KEY, S3_PRIVATE_KEY)
fz_s3_bucket = s3_connection.get_bucket("fz-images")

#connects to the db
fz_images_db = im_db(db_PUBLIC_KEY, db_PRIVATE_KEY)

def remove_latest_zoom():
	name = fz_images_db.getimagenames(1)[0][1]+".gif"
	fz_s3_bucket.delete_key(name)
	fz_images_db.removelatest()
	print("latest zoom removed")

def compress_s3():
	"""applies compression to all items in s3, shouldn't EVER need to be run again"""
	all_images = fz_s3_bucket.get_all_keys()
	n = 0
	for image in all_images:
		n+=1
		test_image = image
		print(n,"::Working on:", test_image)
		#test_image.get_contents_to_filename("current.gif")
		print(n,"::Got it...")
		#os.system("convert {0} -layers Optimize {0}".format("current.gif"))
		print(n,"::Optimized it...")
		#test_image.set_contents_from_filename("current.gif")
		#test_image.make_public()
		print(n,"::Saved it back to s3...")
		#os.remove("current.gif")
		print(n,"::Removed from local filesystem.  Moving on to next image.")





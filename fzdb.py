from boto import dynamodb
import boto

class im_db:
	def __init__(self, db_PUBLIC_KEY, db_PRIVATE_KEY):
		"""sets up connection and updates the latest counter"""
		self.db_connection = dynamodb.connect_to_region('us-east-1',aws_access_key_id=db_PUBLIC_KEY,aws_secret_access_key=db_PRIVATE_KEY)
		self.imtable = self.db_connection.get_table('fzimages')
		self.updatelatest()
	def updatelatest(self):
		"""updates the variable self.latest to the db"""
		self.dbitem_latest = self.imtable.get_item(0)
		self.latest = self.dbitem_latest['most reacent']

	def inclatest(self, num=1):
		"""increments latest counter in the db"""
		self.dbitem_latest.add_attribute("most reacent", num)
		self.dbitem_latest.save()
		self.latest += 1

	def removelatest(self):
		self.imtable.get_item(self.latest).delete()
		self.dbitem_latest.add_attribute("most reacent", -1)
		self.dbitem_latest.save()
		self.latest -= 1

	def addimage(self, s3id):
		"""given an id, adds the item to the db and increments the db count"""
		self.imtable.new_item(hash_key = self.latest+1, attrs= {"s3id" : s3id}).put()
		self.inclatest() #if more than one server is used, this needs to be changed :P

	def getimagesrange(self, start=0, number=10):
		"""start is the number of images back, then number is how many to grab (going futher back)"""
		image_nums = [n for n in range(self.latest-start-number+1, self.latest-start+1)]
		results_dict = self.imtable.batch_get_item(image_nums)

		if self.latest-start < 1:
			return []	

		result_list = []
		for item in results_dict:
			if item['photo number'] >= 1:
				result_list.append([item['photo number'], str(item['s3id'])])
		#
		return sorted(result_list)


	def getimagenames(self, num=10):
		"""returns the (Defult) 10 latest items from the db"""
		results_dict = self.imtable.batch_get_item([n for n in range(self.latest-num+1, self.latest+1)])
		return sorted([[item['photo number'], str(item['s3id'])] for item in results_dict])

	def getimagespage(self, page=0, pagelength=10):
		"""returns pageinated results"""
		if page*pagelength > self.latest:
			return []
		return self.getimagesrange(page*pagelength, pagelength)

"""
#adds all from s3
S3_PUBLIC_KEY = "AKIAIWHKKSAX2GVRHUZQ"
S3_PRIVATE_KEY = "mruUXSnyXU6ylrR3/ZAn66ND82YF4Vjkt/KSM5/W"

#setup for the connection to s3
s3_connection = boto.connect_s3(S3_PUBLIC_KEY, S3_PRIVATE_KEY)
fz_s3_bucket = s3_connection.get_bucket("fz-images")

images = fz_s3_bucket.list()


for key in images:
   db_fz.addimage(key.name[:-4])"""
from PIL import Image, ImageSequence, ImageEnhance
from images2gif import writeGif
import PIL, random, string, exifread

def makegif(jpg_file_name, result_file_name):
	temp_image = Image.open(jpg_file_name)

	#rotates weird iphone images correctly
	try:
		f = open(jpg_file_name, 'rb')
		tags = exifread.process_file(f)
		f.close()
		if str(tags['Image Orientation']) == 'Rotated 90 CCW':
			temp_image = temp_image.rotate(-90)
		if str(tags['Image Orientation']) == 'Rotated 90 CW':
			temp_image = temp_image.rotate(90)
	except KeyError:
		pass

	#resizes images to a basewidth of 640px
	basewidth = 640
	wpercent = (basewidth/float(temp_image.size[0]))
	hsize = int((float(temp_image.size[1])*float(wpercent)))
	temp_image = temp_image.resize((basewidth,hsize), PIL.Image.ANTIALIAS)

	#time in between frames
	original_duration = 0.14

	#generate fames to be put into gif
	w,h = temp_image.size
	frames = [temp_image.copy()]
	mult = 38
	for x in range(1,3):
		x = x * mult
		temp_image = temp_image.crop((29,29,w-x*w/h,h-x*h/w))
		sharpener = ImageEnhance.Sharpness(temp_image.convert('RGB'))
		temp_image = sharpener.enhance(1)
		temp_image = temp_image.resize((w, h), Image.ANTIALIAS)
		temp_image = temp_image.rotate(2)
		frames.append(temp_image.copy())

	#sets gif filename
	gif_file_name = result_file_name.rsplit('.', 1)[0] + ".gif"

	#writes gif to file
	writeGif(gif_file_name, frames, duration=original_duration, dither=0)

	#returns the file name, this isn't really nessicary sense we gave it a file name initially and they just have different extenions (.*** in .gif out)
	return gif_file_name

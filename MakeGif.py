from PIL import Image, ImageSequence, ImageEnhance
from images2gif import writeGif
import PIL, random, string, fix_orientation

def makegif(in_file):
	temp_image = Image.open(in_file)
	#temp_image = Image.open(in_file)

	#rotates weird iphone images correctly
	temp_image = temp_image.rotate(fix_orientation.fix_orientation(temp_image)[1])

	#resizes images to a basewidth of 640px
	basewidth = 320
	wpercent = (basewidth/float(temp_image.size[0]))
	hsize = int((float(temp_image.size[1])*float(wpercent)))
	temp_image = temp_image.resize((basewidth,hsize), PIL.Image.ANTIALIAS)

	#time in between frames
	original_duration = 0.155

	#generate fames to be put into gif
	w,h = temp_image.size
	frames = [temp_image.copy()]
	mult = 17.5
	for x in range(1,3):
		x = x * mult
		temp_image = temp_image.rotate(1.5)
		temp_image = temp_image.crop((29,29,w-x*w/h,h-x*h/w))
		sharpener = ImageEnhance.Sharpness(temp_image.convert('RGB'))
		temp_image = sharpener.enhance(1)
		temp_image = temp_image.resize((w, h), Image.ANTIALIAS)
		frames.append(temp_image.copy())

	#returns a file object of the gif!
	return writeGif(frames, duration=original_duration, dither=0)

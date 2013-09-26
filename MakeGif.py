from PIL import Image, ImageSequence, ImageEnhance
from images2gif import writeGif
import random, string

def makegif(jpg_file_name, result_file_name):
	temp_image = Image.open(jpg_file_name)
	temp_image = temp_image.rotate(-90)
	temp_image = temp_image.resize((720, 960), Image.ANTIALIAS)
	
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

	gif_file_name = result_file_name.rsplit('.', 1)[0] + ".gif"
	#writes gif to file
	writeGif(gif_file_name, frames, duration=original_duration, dither=0)

	return gif_file_name


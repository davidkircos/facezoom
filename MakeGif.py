from PIL import Image, ImageSequence, ImageEnhance
from images2gif import writeGif
import random, string

def makegif(jpg_file_name):
	temp_file_name = ''.join(random.sample(string.ascii_letters+string.digits,10))+'.gif'
	temp_image = Image.open(jpg_file_name)
	temp_image = temp_image.rotate(-90)
	
	original_duration = 0.14

	#generate fames to be put into gif
	w,h = temp_image.size
	frames = [temp_image.copy()]
	mult = 30
	for x in range(1,3):
		x = x * mult
		temp_image = temp_image.crop((20,15,w-x*w/h,h-x*h/w))
		sharpener = ImageEnhance.Sharpness(temp_image.convert('RGB'))
		temp_image = sharpener.enhance(1)
		temp_image = temp_image.rotate(2)
		temp_image = temp_image.resize((w, h), Image.ANTIALIAS)
		frames.append(temp_image.copy())

	#write animated gif
	gif_file_name = 'static/' + ''.join(random.sample(string.ascii_letters+string.digits,10))+'.gif'
	writeGif(gif_file_name, frames, duration=original_duration, dither=0)

	return gif_file_name[7:]

print(makeGif("photo (1).JPG"))

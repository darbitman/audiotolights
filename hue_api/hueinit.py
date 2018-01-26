import PhilipsHue
import time

def hueinit():
	Hue = PhilipsHue.Bridge(cfg_file)
	return Hue

cfg_file = str()
if __name__ == "__main__":
	print("calling hueinit")
	cfg_file = "config.txt"
	Hue = hueinit()
	Hue.get_light_names()
	while(1):
		pass
		#Hue.set_light(1, True, 1, 1)
		#time.sleep(0.1)
		#Hue.set_light(1, True, 254, 1)
		#time.sleep(0.1)
else:
	print("importing hueinit")
	cfg_file = "hue_api/config.txt"

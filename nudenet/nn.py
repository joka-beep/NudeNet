import sys
import os
from detector import Detector
import argparse


def images_in(path):
	filenames = []
	if os.path.isdir(path):
		print("Filenames: ")
		filenames = []
		for root, dirs, files in os.walk(path):
			for f in files:
				filenames.append(os.path.abspath(os.path.join(path, f)))
	elif os.path.isfile(path):
		filenames.append(path)
	else:
		print("path invalid")

	images = [f for f in filenames if f.lower().endswith(".jpg") or f.lower().endswith(".png") or f.lower().endswith(".jpeg")]

	print(images)
	return images


def main(args):
	images = images_in(args.input)

	detector = Detector()
	exposed_parts = ["EXPOSED_ANUS", "EXPOSED_BUTTOCKS", "EXPOSED_BREAST_F", "EXPOSED_GENITALIA_F"]
	covered_parts =["COVERED_BUTTOCKS", "COVERED_BREAST_F", "COVERED_GENITALIA_F"]

	if args.strict:
		to_blur = exposed_parts + covered_parts
	elif args.casual:
		to_blur = ["EXPOSED_BREAST_F", "EXPOSED_GENITALIA_F"]
	else:
		to_blur = exposed_parts

	for f in images:
		path, filename = os.path.split(f)
		name, extension = os.path.splitext(filename)
		detector.censor(f, out_path=name+"_censored"+extension, visualize=False, parts_to_blur=to_blur, with_stamp=args.stamped)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', '--input')
	parser.add_argument('-o', '--output', required=False)
	parser.add_argument('-s', '--strict', action="store_true", default=False)
	parser.add_argument('-c', '--casual', action="store_true", default=False)
	parser.add_argument('--stamped', action="store_true", default=False)
	args = parser.parse_args()
	print(args)
	main(args)

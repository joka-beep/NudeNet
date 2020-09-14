import sys
import os
from detector import Detector


def files_in(directory):
	print("Filenames: ")
	filenames = []
	for root, dirs, files in os.walk(directory):
		for f in files:
			filenames.append(os.path.abspath(os.path.join(directory, f)))
	print(filenames)
	return filenames


def main(argv):
	files = files_in(argv)

	selected_files = [f for f in files if f.endswith(".jpg") or f.endswith(".png") or f.endswith(".jpeg")]

	detector = Detector()
	censored_parts = ["EXPOSED_BUTTOCKS", "EXPOSED_BREAST_F", "EXPOSED_GENITALIA_F", "EXPOSED_ANUS", "EXPOSED_BUTTOCKS", "EXPOSED_BREAST_F"]
	covered_parts =["COVERED_BUTTOCKS", "COVERED_BREAST_F", "COVERED_GENITALIA_F"]
	

	for f in selected_files:
		path, filename = os.path.split(f)
		detector.censor(f, out_path=filename, visualize=False, parts_to_blur=censored_parts+covered_parts)


if __name__ == "__main__":
	main(sys.argv[1])

import os
import keras
import pydload
from keras_retinanet import models
from keras_retinanet.utils.image import preprocess_image, resize_image
from keras_retinanet.utils.visualization import draw_box, draw_caption
from keras_retinanet.utils.colors import label_color

from video_utils import get_interest_frames_from_video

import cv2
import numpy as np

import logging

from PIL import Image as pil_image

from progressbar import progressbar


def read_image_bgr(path):
    """ Read an image in BGR format.
    Args
        path: Path to the image.
    """
    if isinstance(path, str):
        image = np.ascontiguousarray(pil_image.open(path).convert("RGB"))
    else:
        path = cv2.cvtColor(path, cv2.COLOR_BGR2RGB)
        image = np.ascontiguousarray(pil_image.fromarray(path))

    return image[:, :, ::-1]


def dummy(x):
    return x


FILE_URLS = {
    "default": {
        "checkpoint": "https://github.com/notAI-tech/NudeNet/releases/download/v0/detector_v2_default_checkpoint",
        "classes": "https://github.com/notAI-tech/NudeNet/releases/download/v0/detector_v2_default_classes",
    },
    "base": {
        "checkpoint": "https://github.com/notAI-tech/NudeNet/releases/download/v0/detector_v2_base_checkpoint",
        "classes": "https://github.com/notAI-tech/NudeNet/releases/download/v0/detector_v2_base_classes",
    },
}


class Detector:
    detection_model = None
    classes = None

    def __init__(self, model_name="default"):
        """
            model = Detector()
        """
        checkpoint_url = FILE_URLS[model_name]["checkpoint"]
        classes_url = FILE_URLS[model_name]["classes"]

        home = os.path.expanduser("~")
        model_folder = os.path.join(home, f".NudeNet/{model_name}")
        if not os.path.exists(model_folder):
            os.makedirs(model_folder)

        checkpoint_path = os.path.join(model_folder, "checkpoint")
        classes_path = os.path.join(model_folder, "classes")

        if not os.path.exists(checkpoint_path):
            print("Downloading the checkpoint to", checkpoint_path)
            pydload.dload(checkpoint_url, save_to_path=checkpoint_path, max_time=None)

        if not os.path.exists(classes_path):
            print("Downloading the classes list to", classes_path)
            pydload.dload(classes_url, save_to_path=classes_path, max_time=None)

        
        self.detection_model = models.load_model(
            checkpoint_path, backbone_name="resnet50"
        )
        self.classes = [
            c.strip() for c in open(classes_path).readlines() if c.strip()
        ]

    def detect_video(self, video_path, min_prob=0.6, batch_size=2, show_progress=True):
        frame_indices, frames, fps, video_length = get_interest_frames_from_video(
            video_path
        )
        logging.debug(
            f"VIDEO_PATH: {video_path}, FPS: {fps}, Important frame indices: {frame_indices}, Video length: {video_length}"
        )
        frames = [read_image_bgr(frame) for frame in frames]
        frames = [preprocess_image(frame) for frame in frames]
        frames = [resize_image(frame) for frame in frames]
        scale = frames[0][1]
        frames = [frame[0] for frame in frames]
        all_results = {
            "metadata": {
                "fps": fps,
                "video_length": video_length,
                "video_path": video_path,
            },
            "preds": {},
        }

        progress_func = progressbar

        if not show_progress:
            progress_func = dummy

        for _ in progress_func(range(int(len(frames) / batch_size) + 1)):
            batch = frames[:batch_size]
            batch_indices = frame_indices[:batch_size]
            frames = frames[batch_size:]
            frame_indices = frame_indices[batch_size:]
            if batch_indices:
                boxes, scores, labels = self.detection_model.predict_on_batch(
                    np.asarray(batch)
                )
                boxes /= scale
                for frame_index, frame_boxes, frame_scores, frame_labels in zip(
                    frame_indices, boxes, scores, labels
                ):
                    if frame_index not in all_results["preds"]:
                        all_results["preds"][frame_index] = []

                    for box, score, label in zip(
                        frame_boxes, frame_scores, frame_labels
                    ):
                        if score < min_prob:
                            continue
                        box = box.astype(int).tolist()
                        label = self.classes[label]

                        all_results["preds"][frame_index].append(
                            {"box": box, "score": score, "label": label}
                        )

        return all_results

    def detect(self, img_path, min_prob=0.6):
        image = read_image_bgr(img_path)
        image = preprocess_image(image)
        image, scale = resize_image(image)
        boxes, scores, labels = self.detection_model.predict_on_batch(
            np.expand_dims(image, axis=0)
        )
        boxes /= scale
        processed_boxes = []
        for box, score, label in zip(boxes[0], scores[0], labels[0]):
            if score < min_prob:
                continue
            box = box.astype(int).tolist()
            label = self.classes[label]
            processed_boxes.append({"box": box, "score": score, "label": label})

        return processed_boxes

    @staticmethod
    def pixelize(image, blocks=7):
        # divide the input image into NxN blocks
        (h, w) = image.shape[:2]
        xSteps = np.linspace(0, w, blocks + 1, dtype="int")
        ySteps = np.linspace(0, h, blocks + 1, dtype="int")
        # loop over the blocks in both the x and y direction
        for i in range(1, len(ySteps)):
            for j in range(1, len(xSteps)):
                # compute the starting and ending (x, y)-coordinates
                # for the current block
                startX = xSteps[j - 1]
                startY = ySteps[i - 1]
                endX = xSteps[j]
                endY = ySteps[i]
                # extract the ROI using NumPy array slicing, compute the
                # mean of the ROI, and then draw a rectangle with the
                # mean RGB values over the ROI in the original image
                roi = image[startY:endY, startX:endX]
                (B, G, R) = [int(x) for x in cv2.mean(roi)[:3]]
                cv2.rectangle(image, (startX, startY), (endX, endY),
                              (B, G, R), -1)
        # return the pixelated blurred image
        return image

    def censor(self, img_path, out_path=None, visualize=False, parts_to_blur=[], with_stamp=False):
        if not out_path and not visualize:
            print(
                "No out_path passed and visualize is set to false. There is no point in running this function then."
            )
            return

        image = cv2.imread(img_path)
        boxes = self.detect(img_path)
        print(boxes)



        if parts_to_blur:
            boxes = [i for i in boxes if i["label"] in parts_to_blur]
        else:
            boxes = [i for i in boxes]

        #put pussy at the end so that the stamp is not distorted
        genitalia = [i for i in boxes if i["label"] == "EXPOSED_GENITALIA_F"]
        boxes = [i for i  in boxes if i["label"] != "EXPOSED_GENITALIA_F"]
        boxes += genitalia

        for item in boxes:
            box = item["box"]
            part = image[box[1] : box[3], box[0] : box[2]]
            part = self.pixelize(part)
            image[box[1]:box[3], box[0]:box[2]] = part

            if with_stamp:
                stamp = cv2.imread("/home/jonas/.data/Pictures/censorator/wip/stamp.png", -1)
                if item["label"] == "EXPOSED_GENITALIA_F":
                    #rectangle to square conversion with average sizes
                    x_dimensions = abs(box[0]-box[2])
                    y_dimensions = abs(box[1]-box[3])
                    dimensions = int( (x_dimensions + y_dimensions) / 2)

                    # calculate the offset including medium error due to rectangle to square conversion
                    offset_x = min(box[0], box[2]) + int((x_dimensions-dimensions)/2)
                    offset_y = min(box[1], box[3]) + int((y_dimensions-dimensions)/2)

                    s_img = cv2.resize(stamp, (dimensions, dimensions), interpolation=cv2.INTER_AREA)

                    alpha_s = s_img[:, :, 3] / 255.0
                    alpha_l = 1.0 - alpha_s
                    for c in range(0, 3):
                        image[offset_y:offset_y+dimensions, offset_x:offset_x+dimensions, c] = (alpha_s * s_img[:, :, c] +
                                                                  alpha_l * image[offset_y:offset_y+dimensions, offset_x:offset_x+dimensions, c])

        if visualize:
            cv2.imshow("Blurred image", image)
            cv2.waitKey(0)

        if out_path:
            cv2.imwrite(out_path, image)


if __name__ == "__main__":
    m = Detector()
    print(m.detect("/Users/bedapudi/Desktop/n2.jpg"))

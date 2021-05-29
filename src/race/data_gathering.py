import cv2
from tqdm import tqdm
from glob import glob
import os
import numpy as np
import json

with open("config.json", "rb") as f:
    config = json.load(f)

step = config["race_gathering"]["step"]
start_offset = config["race_gathering"]["start_offset_min"] * 60
end_offset = config["race_gathering"]["end_offset_min"] * 60
res_mul = config["resolution"] / 720


def gather_screenshots(video_path: str):
    global step, start_offset, end_offset
    cap = cv2.VideoCapture(video_path)
    currentframe = 0
    frames_per_second = cap.get(cv2.CAP_PROP_FPS)
    start_offset *= frames_per_second
    end_offset *= frames_per_second
    frames_count = int((cap.get(cv2.CAP_PROP_FRAME_COUNT) - start_offset - end_offset) / (step * frames_per_second))
    started = False
    frames_captured = 0
    base_dir = "screenshots"

    screenshots = glob(base_dir + "/drivers/*") + glob(base_dir + "/sectors/*")
    for screenshot in screenshots:
        os.remove(screenshot)
    print(f"Removed {len(screenshots)} existing screenshots.")

    with tqdm(total=frames_count, position=0, leave=True, ascii=True) as progress_bar:
        while True:
            ret, frame = cap.read()
            if ret:
                if currentframe > start_offset or started:
                    started = True
                    if currentframe > (step * frames_per_second):
                        currentframe = 0

                        drivers_and_sectors = frame[int(107*res_mul):int(525*res_mul), int(106*res_mul):int(1215*res_mul)]
                        drivers = drivers_and_sectors[:, :int(42*res_mul)]
                        sectors = drivers_and_sectors[:, int(910*res_mul):]

                        red_flag_frame = frame[int(35*res_mul):int(60*res_mul), int(285*res_mul):int(800*res_mul)]
                        red_flag_frame_hsv = cv2.cvtColor(red_flag_frame, cv2.COLOR_BGR2HSV)

                        # Lower mask (0-5) and upper mask (175-180) (RED)
                        mask1 = cv2.inRange(red_flag_frame_hsv, (0, 50, 20), (5, 255, 255))
                        mask2 = cv2.inRange(red_flag_frame_hsv, (175, 50, 20), (180, 255, 255))
                        mask = cv2.bitwise_or(mask1, mask2)
                        red_flag = cv2.bitwise_and(red_flag_frame, red_flag_frame, mask=mask)

                        if np.count_nonzero(red_flag) == 0:
                            cv2.imwrite(base_dir + "/drivers/" + str(frames_captured) + ".png", drivers)
                            cv2.imwrite(base_dir + "/sectors/" + str(frames_captured) + ".png", sectors)

                        frames_captured += 1
                        progress_bar.update(1)
                currentframe += 1
            else:
                break

    list(getattr(tqdm, '_instances'))
    for instance in list(tqdm._instances):
        tqdm._decr_instances(instance)

    cap.release()
    cv2.destroyAllWindows()

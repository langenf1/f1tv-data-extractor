from math import ceil, floor
import random
from typing import List
import numpy as np
import pickle
import glob
import cv2 as cv
from PIL import Image
import pytesseract
import re
import difflib
import os
from tqdm import tqdm
import json

with open("config.json", "rb") as f:
    config = json.load(f)

recursion_limit = 20
recursions = 0

drivers_on_grid = config["race_processing"]["drivers_on_grid"]
res_mul = config["resolution"] / 720


def preprocess_image(image_path: str, resize_scale: float, contrast: bool):
    image = cv.imread(image_path)
    image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    image = cv.resize(image, None, fx=resize_scale, fy=resize_scale)
    if contrast:
        image = cv.convertScaleAbs(image, alpha=2, beta=0)
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    image = cv.filter2D(image, -1, kernel)
    return image


def parse_drivers(image_path: str, resize_scale: int = 4):
    all_data = []
    drivers = preprocess_image(image_path, resize_scale, contrast=True)
    drivers = split_drivers_image(drivers, resize_scale)

    for driver in drivers:
        pixel_is_not_black = np.array([value > 200 for value in [row for row in driver]])
        if pixel_is_not_black.any():
            driver_data = pytesseract.image_to_string(
                Image.fromarray(driver),
                lang='eng',
                config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVW'
            )
            all_data.append(driver_data)
        else:
            all_data.append("")

    all_data = [driver.strip('\f').strip('\n')[:3] for driver in all_data]
    assert len(all_data) == drivers_on_grid

    # Spellchecking
    drivers = [x["name"] for x in config["drivers"]]
    for i in range(len(all_data)):
        if all_data[i] not in drivers:
            closest_matches = difflib.get_close_matches(all_data[i], drivers)
            if len(closest_matches) < 1:
                global recursion_limit, recursions
                if recursions < recursion_limit:
                    recursions += 1
                    return parse_drivers(image_path, resize_scale=random.randint(2, 10))
                else:
                    return []
            else:
                # print(all_data[i] + " -> " + closest_matches[0])
                all_data[i] = closest_matches[0]

    print("Parsed drivers: ", all_data)
    return all_data


def parse_sectors(image_path: str):
    all_data = []
    resize_scale = 4
    sectors = preprocess_image(image_path, resize_scale, contrast=True)
    sectors = split_sectors_image(sectors, resize_scale)

    for i in range(drivers_on_grid):
        all_data.append({})
        for j in range(3):
            pixel_is_not_black = np.array([value > 200 for value in [row for row in sectors[(i*3)+j]]])
            if pixel_is_not_black.any():
                sector_data = pytesseract.image_to_string(
                    Image.fromarray(sectors[(i*3)+j]),
                    lang='eng',
                    config='--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789. '
                )

                sector_data = re.findall('......', sector_data)
                all_data[i][j+1] = sector_data[0] if len(sector_data) > 0 else '0'
            else:
                all_data[i][j+1] = '0'

    for line_idx in range(len(all_data)):
        for sector_idx in [1, 2, 3]:
            try:
                try:
                    all_data[line_idx][sector_idx] = float(all_data[line_idx][sector_idx])
                except TypeError:
                    all_data[line_idx][sector_idx] = float(all_data[line_idx][sector_idx][0])

            except ValueError:
                os.system("")
                print(f"WARNING: Sector parsing failure in {image_path}: {all_data[line_idx][sector_idx]}")
                all_data[line_idx][sector_idx] = 0

    return all_data


def get_consecutive_sectors(old_sectors, new_sectors):
    if old_sectors == new_sectors:
        return new_sectors

    for i in range(min(len(new_sectors), len(old_sectors))):
        for sec in [1, 2, 3]:
            if sec in new_sectors[i] and sec in old_sectors[i]:
                if new_sectors[i][sec] != old_sectors[i][sec]:
                    new_sectors[i][sec] = 0

    return new_sectors


def limit_sector_times(sectors):
    for driver_index in range(len(sectors)):
        for sector in [1, 2, 3]:
            if sector in sectors[driver_index]:
                if not 10 < sectors[driver_index][sector] < 100:
                    sectors[driver_index][sector] = 0

    return sectors


def check_almost_equal(old_sectors, new_sectors, total_allowed_diff_sec=1):
    if old_sectors == new_sectors:
        return True

    diff = 0
    if abs(len(new_sectors) - len(old_sectors)) > 1:
        return False
    else:
        for i in range(min(len(new_sectors), len(old_sectors))):
            for sec in [1, 2, 3]:
                if sec in new_sectors[i] and sec in old_sectors[i]:
                    if new_sectors[i][sec] != old_sectors[i][sec]:
                        diff += abs(new_sectors[i][sec] - old_sectors[i][sec])

    return diff < total_allowed_diff_sec


def get_changed_data(all_data, new_data):
    if all_data == new_data:
        return new_data

    for driver in new_data.keys():
        for sec in [1, 2, 3]:
            if driver in all_data:
                if sec in new_data[driver] and sec in all_data[driver]:
                    if new_data[driver][sec] == find_last_real_time(all_data[driver][sec]):
                        new_data[driver][sec] = 0

    return new_data


def find_last_real_time(sectors: List[float]):
    for i in reversed(range(len(sectors))):
        if sectors[i] > 0:
            return sectors[i]
    return 0


def split_drivers_image(preprocessed_image, resize_scale: int = 1):
    pixels_per_driver = floor(21 * resize_scale * res_mul)
    driver_images = []
    for driver_idx in range(ceil(len(preprocessed_image) / pixels_per_driver)):
        if driver_idx == drivers_on_grid - 1:
            driver = preprocessed_image[driver_idx * pixels_per_driver:, :]
        else:
            driver = preprocessed_image[driver_idx * pixels_per_driver:driver_idx * pixels_per_driver + pixels_per_driver, :]
        driver_images.append(driver)

    assert(len(driver_images) == drivers_on_grid)
    return driver_images


def split_sectors_image(preprocessed_image, resize_scale: int = 1):
    pixels_per_driver = floor(21 * resize_scale * res_mul)
    pixels_per_sector = floor(70 * resize_scale * res_mul)
    sector_images = []
    for sector_idx in range(3):
        for driver_idx in range(ceil(len(preprocessed_image) / pixels_per_driver)):
            if driver_idx == drivers_on_grid - 1:
                sector = preprocessed_image[driver_idx * pixels_per_driver:, sector_idx * pixels_per_sector:sector_idx * pixels_per_sector + pixels_per_sector]
            else:
                sector = preprocessed_image[driver_idx * pixels_per_driver:driver_idx * pixels_per_driver + pixels_per_driver,
                         sector_idx * pixels_per_sector:sector_idx * pixels_per_sector + pixels_per_sector]
            sector_images.append(sector)

    assert (len(sector_images) == drivers_on_grid * 3)
    sector_images = np.array(list(zip(sector_images[0:drivers_on_grid],
                                      sector_images[drivers_on_grid:drivers_on_grid*2],
                                      sector_images[drivers_on_grid*2:drivers_on_grid*3])), dtype=object).flatten()
    return sector_images


def process_screenshots():
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        print("WARNING: Could not find Tesseract-OCR 5.0.0 installation path.")

    source_path = "screenshots"
    driver_screenshots = [img for img in sorted(glob.glob(f'{source_path}/drivers/*.png'), key=os.path.getmtime)]
    sector_screenshots = [img for img in sorted(glob.glob(f'{source_path}/sectors/*.png'), key=os.path.getmtime)]
    total_screenshots = min(len(driver_screenshots), len(sector_screenshots))

    all_data = {}
    previous_sec = []
    for driver_ss, sector_ss in tqdm(zip(driver_screenshots, sector_screenshots), total=total_screenshots):
        dri = parse_drivers(driver_ss)
        sec = parse_sectors(sector_ss)
        sec = limit_sector_times(sec)

        if check_almost_equal(previous_sec, sec):
            continue

        previous_sec = sec
        if len(dri) == 0 or len(sec) == 0:
            continue

        combined_data = dict(zip(dri, sec))
        combined_data = get_changed_data(all_data, combined_data)

        for key in combined_data:
            if key in all_data:
                for sector in combined_data[key].keys():
                    if sector in all_data[key]:
                        all_data[key][sector].append(combined_data[key][sector])
                    else:
                        all_data[key][sector] = [combined_data[key][sector]]
            else:
                all_data[key] = {sec: [time] for sec, time in combined_data[key].items()}

    print("Processed Sector Data: ", all_data)

    outfile = open('output/sector_data', 'wb')
    pickle.dump(all_data, outfile)
    outfile.close()

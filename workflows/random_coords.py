import logging

import cv2
import numpy as np
import random

def gen_random_coordinates(data, img_path, mask_path, count=0):
    """
    RANDOM COORDS GENERATOR
    _______________________________
    @data: dataframe with coordinates scaled to whatever format desired
    @img_path: path to image we are finding the n nearest distance of (only needed if gen_rand is True)
    @mask_path: path to mask we are finding the n nearest distance of (only needed if gen_rand is True)
    @count: number of random particles to generate
    """
    def generate_random_points(boundary, quantity, mask):
        # generate faux particles within the pface
        coords = []
        num = 0
        while num <= quantity:
            x = random.randint(1, boundary[0] - 1)
            y = random.randint(1, boundary[1] - 1)
            if mask[x, y] != 0:
                coords.append((x, y))
                num += 1
        # print(f"The total number of particles inside the p-face are {count}.")
        return coords
    x_coordinates = np.array(data['X'])
    y_coordinates = np.array(data['Y'])
    read_coords = []
    for i in range(len(x_coordinates)):
        read_coords.append((float(y_coordinates[i]), float(x_coordinates[i])))
    # import img
    img_original = cv2.imread(img_path)
    crop = img_original.shape
    img_pface = cv2.imread(mask_path)
    img_pface = img_pface[:crop[0], :crop[1], :3]
    # grab contours of pface
    lower_bound = np.array([239, 174, 0])
    upper_bound = np.array([254, 254, 254])
    pface_mask = cv2.inRange(img_pface, lower_bound, upper_bound)
    logging.info("generated random particles")
    return generate_random_points(pface_mask.shape, count, pface_mask)

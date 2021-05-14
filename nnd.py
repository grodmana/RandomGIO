import cv2
import numpy as np
import random
import pandas as pd
import math

from typings import Unit

""" 
N NEAREST DISTANCE RUN FUNCTION
_______________________________
@prog_wrapper: progress bar wrapper element, allows us to track how much time is left in process
@data: dataframe with coordinates scaled to whatever format desired
@gen_rand: generate random coordinates
@img_path: path to image we are finding the n nearest distance of (only needed if gen_rand is True)
@pface_path: path to mask we are finding the n nearest distance of (only needed if gen_rand is True)
@csv_scalar: optional scalar prop to multiply all csv coordinate values by
"""
def run_nnd(data, prog_wrapper, gen_real=True, gen_rand=False, img_path="", pface_path="", n_rand_to_gen=None):
    # Generate Faux Gold Particles within the P-face
    def generate_random_points(boundary, quantity, mask):
        coordinates = []
        count = 0
        while count <= quantity:
            x = random.randint(1, boundary[0] - 1)
            y = random.randint(1, boundary[1] - 1)
            if mask[x, y] != 0:
                coordinates.append((x, y))
                count += 1
        print(f"The total number of particles inside the p-face are {count}.")
        return coordinates

    """ FIND DIST TO CLOSEST PARTICLE """
    def distance_to_closest_particle(coord_list):
        nndlist = []
        coord_list_len = len(coord_list)
        for i in range(coord_list_len - 1):
            # update progress bar
            prog_wrapper.update_progress(i)
            small_dist = 10000000000000000000
            # templist = [og coord (x, y), closest coord (x, y), distance]
            templist = [0, 0, 0]
            particle_i = coord_list[i]
            particle_if = (particle_i[1], particle_i[0])
            templist[0] = particle_if
            for j in range(0, coord_list_len - 1):
                if i is not j:
                    particle_j = coord_list[j]
                    particle_jf = (particle_j[1], particle_j[0])
                    dist = ((particle_jf[0] - particle_if[0]) ** 2) + ((particle_jf[1] - particle_if[1]) ** 2)
                    dist = math.sqrt(dist)
                    if (dist < small_dist):
                        small_dist = dist
                        templist[1] = particle_jf
                        templist[2] = small_dist
            nndlist.append(templist)

        return nndlist

    """ N NEAREST DISTANCE """
    def nnd(coordinate_list, pface_mask=None):
        # print("mask", pface_mask, pface_mask.shape)
        print("running nnd")
        real_nndlist = distance_to_closest_particle(coordinate_list)
        d = {'Nearest Neighbor Distance': real_nndlist}
        real_df = pd.DataFrame(data=d)
        clean_rand_df = pd.DataFrame([])

        if len(pface_path) > 0 and len(img_path) > 0:
            n_to_gen = int(n_rand_to_gen) if n_rand_to_gen is not None and len(n_rand_to_gen) > 0 else len(coordinate_list)
            randomcoords = generate_random_points(pface_mask.shape, n_to_gen, pface_mask)
            # print("rand coords", randomcoords)
            random_nndlist = distance_to_closest_particle(randomcoords)
            d = {'Nearest Neighbor Distance': random_nndlist}
            rand_df = pd.DataFrame(data=d)

            clean_rand_df = pd.DataFrame()
            clean_rand_df[['og_coord', 'closest_coord', 'dist']] = pd.DataFrame(
                [x for x in rand_df['Nearest Neighbor Distance'].tolist()])

        # print("rand", rand_df.head())
        # clean up df
        clean_real_df = pd.DataFrame()
        clean_real_df[['og_coord', 'closest_coord', 'dist']] = pd.DataFrame(
            [x for x in real_df['Nearest Neighbor Distance'].tolist()])
        return clean_real_df, clean_rand_df

    """ START """
    # # Import CSV Coordinates
    # data = pd.read_csv(csv_path, sep=",", header=None)
    x_coordinates = np.array(data['X'])
    y_coordinates = np.array(data['Y'])
    real_coordinates = []
    for i in range(len(x_coordinates)):
        real_coordinates.append((round(float(y_coordinates[i])), round(float(x_coordinates[i]))))

    # if generate_random prop enabled, create random coordinates and return results, else return real coordinates
    if len(pface_path) > 0 and len(img_path) > 0:
        # import images
        img_original = cv2.imread(img_path)
        crop = img_original.shape
        img_pface = cv2.imread(pface_path)
        img_pface = img_pface[:crop[0], :crop[1], :3]
        # grab contours of pface
        lower_bound = np.array([239, 174, 0])
        upper_bound = np.array([254, 254, 254])
        pface_mask = cv2.inRange(img_pface, lower_bound, upper_bound)
        pface_cnts, pface_hierarchy = cv2.findContours(pface_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        drawn_pface_mask = img_pface.copy()
        drawn_pface_mask = cv2.drawContours(drawn_pface_mask, pface_cnts, -1, (0, 255, 0), 5)
        pface_area = 0
        for cnt in pface_cnts:
            area = cv2.contourArea(cnt)
            pface_area += area
        return nnd(coordinate_list=real_coordinates, pface_mask=pface_mask)
    else:
        return nnd(coordinate_list=real_coordinates)


""" DRAW LINES TO ANNOTATE N NEAREST DIST ON IMAGE """
def draw_length(nnd_df, bin_counts, img, palette, input_unit='px', scalar=1,  save_img=True):
    def sea_to_rgb(color):
        color = [val * 255 for val in color]
        return color
    count = 0
    bin_idx = 0

    for idx, entry in nnd_df.iterrows():
        count += 1
        particle_1 = entry['og_coord']
        particle_2 = entry['closest_coord']

        if input_unit == 'px':
            particle_1 = tuple(scalar * x for x in particle_1)
            particle_2 = tuple(scalar * x for x in particle_2)
        else:
            particle_1 = tuple(x / scalar for x in particle_1)
            particle_2 = tuple(x / scalar for x in particle_2)

            print("p", particle_1, particle_2)

        if count >= bin_counts[bin_idx]:
            bin_idx += 1
            count = 0
        img = cv2.circle(img, particle_1, 10, (0, 0, 255), -1)
        img = cv2.line(img, particle_1, particle_2, sea_to_rgb(palette[bin_idx]), 5)

    # save image
    if save_img:
        cv2.imwrite('./output/drawn_nnd_img.jpg', img)
    return img
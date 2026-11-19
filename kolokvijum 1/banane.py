# Pri pronalazenju resenja pomogao je Claude Code (AI asistent).
# Pomogao je pri izboru vrednosti HSV maski (zuta, zelena) i granica kontura
# (povrsina, cirkularnost, solidnost) za detekciju 3 glavna objekta:
# banane, grozda banana i banana novcica.
# Formatiranje koda (uvlacenje, prelamanje linija) uradjeno je auto-formaterom.

import sys
import numpy as np
import cv2
import matplotlib
import matplotlib.pyplot as plt
import csv


def load_image(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)


def display_image(image, color=False):
    if color:
        plt.imshow(image)
    else:
        plt.imshow(image, 'gray')


def resenje(source, image, result):
    slika = load_image(source + 'images/' + image)
    # HSV = Hue (nijansa boje), Saturation (zasicenost), Value (osvetljenost).
    # Koristi se jer je boja odvojena od osvetljenja, pa se zuta lakse izdvaja
    # jednim opsegom nijanse nego u RGB, gde senke i odsjaji menjaju sve 3 vrednosti.
    hsv = cv2.cvtColor(slika, cv2.COLOR_RGB2HSV)
    height, width = hsv.shape[0:2]

    # maska za jarko zute piksele (banane, grozdovi, novcici)
    mask = cv2.inRange(hsv, (18, 190, 130), (32, 255, 255))

    # HUD nije "u svetu" - gornji levi (zivoti) i gornji desni ugao (brojac)
    mask[:130, :330] = 0
    mask[:110, 1100:] = 0

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # zelena maska - zuto lisce na platformama je okruzeno zelenim
    green = cv2.inRange(hsv, (34, 80, 40), (90, 255, 255))

    # findContours vraca (contours, hierarchy). Kontura je lista tacaka (x, y)
    # koje opisuju granicu jednog povezanog belog regiona u binarnoj maski.
    # Hierarchy opisuje odnos kontura (roditelj/dete) - ovde se ne koristi (_),
    # jer RETR_EXTERNAL uzima samo spoljne konture.
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    contours_img = []
    vrednost = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 15:
            continue

        # arcLength = obim konture (duzina granice), True = kontura je zatvorena.
        # Cirkularnost = 4*pi*P / O^2 -> za savrsen krug je 1, za izduzene i
        # nazubljene oblike je manja. Koristi se da se novcic (okrugao)
        # razlikuje od grozda banana slicne velicine.
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter)

        # Konveksni omotac (convex hull) = najmanji konveksni oblik oko konture
        # ("gumica rastegnuta oko objekta"), hull_area je njegova povrsina.
        # Solidnost (solidity) = povrsina konture / povrsina omotaca -> koliko objekat
        # "popunjava" svoj omotac. Banane i novcici su kompaktni (veca solidnost),
        # a razgranati ostaci lisca i sum imaju malu solidnost.
        hull_area = cv2.contourArea(cv2.convexHull(contour))
        solidity = area / max(hull_area, 1)

        # maska samo ove konture + prsten oko nje
        x, y, w, h = cv2.boundingRect(contour)
        pad = 8
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(width, x + w + pad), min(height, y + h + pad)
        cmask = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.drawContours(cmask, [contour - [x0, y0]], -1, 255, -1)
        # Prsten oko objekta: dilatacija prosiri objekat za ~5 px na sve strane,
        # pa se od prosirenog oduzme sam objekat -> ostaje samo okolina objekta.
        # Koristi se da se proveri sta se nalazi oko objekta (vidi green_ratio).
        dilated = cv2.dilate(cmask, np.ones((11, 11), np.uint8))
        ring = cv2.subtract(dilated, cmask)

        # Udeo zelenih piksela u prstenu (0 - 1):
        # green[y0:y1, x0:x1] je zelena maska isecena na isti pravougaonik,
        # [ring > 0] uzima samo piksele koji su u prstenu,
        # > 0 daje True/False (zelen ili ne), a .mean() daje udeo True vrednosti.
        # Zuto lisce na platformama je okruzeno zelenim, banane uglavnom nisu.
        # (if ring.any() else 0 - zastita ako je prsten prazan)
        green_ratio = (green[y0:y1, x0:x1][ring > 0] >
                       0).mean() if ring.any() else 0

        # Prosecna nijansa (Hue, kanal 0 u HSV) samo piksela unutar konture.
        # Banane/novcici su ~24-29 (zuto), a narandzasti objekti (biljka,
        # propeleri, oklop puza) imaju manju nijansu, pa se po ovome odbacuju.
        mean_hue = hsv[y0:y1, x0:x1, 0][cmask > 0].mean()

        # odbaci lisce (puno zelenog okolo), narandzaste stvari (biljka, propeleri)
        # i nepravilne oblike
        if green_ratio > 0.5 or mean_hue < 23 or solidity < 0.6:
            continue

        contours_img.append(contour)
        if area >= 500 and circularity >= 0.6:
            vrednost += 10   # banana novcic
        elif area >= 180:
            vrednost += 5    # grozd banana
        else:
            vrednost += 1    # banana

    # debug:
    # img = slika.copy()
    # cv2.drawContours(img, contours_img, -1, (255, 0, 255), 1)
    # display_image(img)
    # plt.show()

    # print(image + f'-{result}-{vrednost}')

    return abs(vrednost - result)


if __name__ == "__main__":

    if len(sys.argv) > 1:

        script_name = sys.argv[0]
        user_argument = sys.argv[1]

        with open(user_argument + 'count.csv', newline='') as csvfile:
            data_reader = csv.reader(csvfile)
            next(data_reader)

            data_list = list(data_reader)
            num_lines = len(data_list)
            result = 0

            for row in data_list:
                image_name, bananas = row
                bananas = int(bananas)
                x = resenje(user_argument, image_name, bananas)
                result += x

            print(f'{result / num_lines}')
    else:
        print("No arguments provided.")

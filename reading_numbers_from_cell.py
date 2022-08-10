"""Moduł odpowiedzialny za zwrócenie wartości jaka jest zapisana w komórce."""

import numpy as np
from datetime import datetime
import match_sign
import cv2
from informing import Informing


class ReadingNumbersFromCell:
    """
    Obiekt do odczytywania wartości z komórek.

    read_number_from_one_digit_cell(np.ndarray) -> str|None - metoda odczytuje wartość z komórki jednocyfrowej
    read_number_from_three_digits_cell(np.ndarray) -> str|None - metoda odczytuje wartość z komórki trzycyfrowej
    """
    def __init__(self, path_dict_with_temp: str, path_dict_with_unrecognized_sign: str,
                 path_dict_with_unrecognized_cell: str, threshold_save_to_dict_with_sign: float,
                 threshold_end_search: float, threshold_save_as_unrecognized: float):
        """
        :param path_dict_with_temp: ścieżka do katalog z przykładowymi znakami
        :param path_dict_with_unrecognized_sign: ścieżka do katalogu z nierozpoznanymi znakami
        :param path_dict_with_unrecognized_cell: ścieżka do katalogu z nierozpoznanymi komórkami
        :param path_dict_with_unrecognized: ścieżka do katalogu z nierozpoznanymi znakami
        :param threshold_end_search: próg po przekroczeniu którego uznaje się, że znak został rozpoznany
        :param threshold_save_to_dict_with_sign: jeżeli został przekrocony threshold_end_search, a ta wartość nie
                                                 zostanie, to obraz zostanie zapisany w katalogu z rozpoznanym znakiem
        :param threshold_save_as_unrecognized: jeżeli nie zostanie przekroczony ten próg to znak zostanie dodany
                                               do katalogu z nierozpoznanymi znakami

        Hierarchia progów:
            threshold_save_to_dict_with_sign >= threshold_end_search > threshold_save_as_unrecognized
        """
        if threshold_save_to_dict_with_sign < threshold_end_search \
                or threshold_end_search <= threshold_save_as_unrecognized:
            raise ValueError("Podane progi w ReadingNumbersFromCell mają nieodpowiednie wartości.")

        obj = match_sign.MatchImgToSign(path_dict_with_temp, path_dict_with_unrecognized_sign, threshold_end_search)
        self.__obj_to_match_sign = obj
        self.__path_dict_with_unrecognized_cell = path_dict_with_unrecognized_cell
        self.__threshold_save_to_dict_with_sign = threshold_save_to_dict_with_sign
        self.__threshold_save_as_unrecognized = threshold_save_as_unrecognized

    def __read_number_from_list_sign(self, list_sign: list[np.ndarray]) -> str | None:
        """
        Metoda odczytuje po kolei zawartość (cyfrę) każdego elementu tablicy obrazów znaków.

        :param list_sign: lista obrazów znaków
        :return: None jeżeli nie rozpoznano jakiegoś znaku, str jeżeli wszystko ok, jeżeli brak znaków to zwróci ""
            Przykładowe zwracane wartości z wyjaśnieniem:
                - None - nie rozpoznano znaku lub znaków w komórce
                - "" - nie ma cyfry w odczytywanej komórce
                - "0" - "999" - wartość odczytana z komórki
        """
        list_digit_details = []
        for sign in list_sign:
            list_digit_details.append(self.__obj_to_match_sign.match_img_to_sign(sign))
        result = ""
        every_ok = True
        for digit_details in list_digit_details:
            if digit_details.matched < self.__threshold_save_as_unrecognized or digit_details.sign is None:
                digit_details.on_add_template_to_unrecognized_sign_folder()
                every_ok = False
            else:
                result += digit_details.sign
        if every_ok:
            return result
        else:
            return None

    def __save_cell_to_dict_with_unrecognized_cell(self, img_cell: np.ndarray) -> None:
        """
        Metoda dodaje obraz komórki do folderu z nierozpoznanymi komórkami.

        Zostaje dodany plik do folderu pod ścieżką self.__path_dict_with_unrecognized_cell.
        Dodany plik w nazwie będzie miał aktualną datę.

        :param img_cell: obraz nierozpoznanego znaku
        """
        name_new_file = datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")
        path = f"{self.__path_dict_with_unrecognized_cell}/{name_new_file}"
        try:
            cv2.imwrite(f"{path}.jpg", img_cell)
            np.save(f"{path}.npy", img_cell)
        except FileNotFoundError:
            Informing().warning(f"Nie można zapisać obrazu pod ścieżką '{path}'")

    def read_number_from_one_digit_cell(self, img_cell: np.ndarray) -> str | None:
        """
        Odczyt numeru z komórki zawierającej jedną cyfrę.

        Taka komórka to np. ta zawierająca informacje o numerze toru, na którym gra zawodnik.
        :param img_cell: obraz komórki
        :return: None jeżeli nie udało nie rozpoznać jakiegoś znaku, str jeżeli wszystko się udało, jeżeli w komórce nie
                 było liczby to zwrócone zostanie ""
        """
        array_sign = self.__cut_signs_from_cell(img_cell, 1)
        result = self.__read_number_from_list_sign(array_sign)
        if result is None:
            self.__save_cell_to_dict_with_unrecognized_cell(img_cell)
        return result

    def read_number_from_three_digits_cell(self, img_cell: np.ndarray) -> str | None:
        """
        Odczyt numeru z komórki zawierającej trzy cyfry.

        Metoda służy do odczytu numeru rzutu lub wyniku gracza, bo te komórki zawierają miejsce na 3 cyfry.
        :param img_cell: obraz komórki
        :return: None jeżeli nie udało nie rozpoznać jakiegoś znaku, str jeżeli wszsytko się udało, jeżeli w komórce nie
                 było liczby to zwrócone zostanie ""
        """
        array_sign = self.__cut_signs_from_cell(img_cell, 3)
        result = self.__read_number_from_list_sign(array_sign)
        if result is None:
            self.__save_cell_to_dict_with_unrecognized_cell(img_cell)
        return result

    def __cut_signs_from_cell(self, img_cell: np.ndarray, number_of_signs: int) -> list[np.ndarray]:
        """
        Metoda odpowiedzialna za wydzielenie z obrazu komórki obrazów ze znakami.

        Dla każdej number_of_signs są inne podziały według tabeli sign_partition.
        Wyjaśnienie:
            Rozmiar znaku jest zmieniany na 28x35, aby po dodaniu białego obramowania miał wymiar 30x37.

        :param img_cell: obraz komórki
        :param number_of_signs: maksymalna liczba cyfr w komórce
        :return: zwraca listę z wyciętymi znakami
        """
        sign_partition = {
            1: {"resize": (100, 100), "partition": [[25, 75]]},
            3: {"resize": (200, 100), "partition": [[50, 99], [98, 147], [146, 194]]}
        }
        array_sign = []
        img_cell = cv2.resize(img_cell, sign_partition[number_of_signs]["resize"], interpolation=cv2.INTER_AREA)

        img_cell = self.__max_rgb_filter(img_cell)
        img_cell = cv2.GaussianBlur(src=img_cell, ksize=(7, 5), sigmaX=0)
        img_cell = cv2.threshold(src=img_cell, thresh=152, maxval=255, type=cv2.THRESH_BINARY)[1]
        img_cell = self.__remove_black_line(img_cell, True)
        img_cell = self.__remove_black_line(img_cell, False)
        img_cell = img_cell[2:69]
        for wsp_x in sign_partition[number_of_signs]["partition"]:
            img_sign = img_cell[:, wsp_x[0]:wsp_x[1]]
            for sign_h in self.__cut_signs(img_sign, False):
                for sign_v in self.__cut_signs(sign_h, True):
                    sign_v = cv2.resize(sign_v, (28, 35), interpolation=cv2.INTER_AREA)
                    sign_v = cv2.copyMakeBorder(sign_v, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=255)
                    array_sign.append(sign_v)
        return array_sign

    @staticmethod
    def __max_rgb_filter(image: np.ndarray) -> np.ndarray:
        """
        Metoda przekształca obraz z BGR, tak że poszczególne pixele będą największą wartością z tych 3 wartości.

        :param image: obraz do przekształcenia
        :return: przekształcony obraz
        """
        (b, g, r) = cv2.split(image)
        m = np.maximum(np.maximum(r, g), b)
        return cv2.merge([m])

    @staticmethod
    def __remove_black_line(img_cell: np.ndarray, cut_vertical: bool) -> np.ndarray:
        """
        Metoda zamienia linie poziome(!cut_vertical) / pionowe(cut_vertical) na białe, jeżeli są białe w mniej niż 20%.

        :param img_cell: obraz jednowymiarowy do przekształcenia
        :param cut_vertical: czy zamiana poziomych linii (False) czy pionowych(True)
        :return: obraz po przekształceniu
        """
        if cut_vertical:
            img_cell = np.rot90(img_cell, 3)
        for i, row in enumerate(img_cell):
            if np.sum(row) < len(row) * 255 * 0.2:
                img_cell[i] = 255
        if cut_vertical:
            img_cell = np.rot90(img_cell)
        return img_cell

    @staticmethod
    def __cut_signs(img: np.ndarray, cut_vertical: bool, min_space: int = 5) -> list[np.ndarray]:
        """
        Metoda dzieląca obraz w poszukiwaniu znaków.

        :param img: obraz komórki
        :param cut_vertical: jeżeli True to poszukiwane są znaki w pionie (obrót o 90 potem 270) jak False to w poziomie
        :param min_space: minimalna różnoca między coord_0 a coord_1 (minimalna szerokość lub wysokość znaku)
        :return: zwraca tablicę ze znalezionymi znakami
        """
        if cut_vertical:
            img = np.rot90(img, 3)
        img = cv2.copyMakeBorder(img, 1, 1, 0, 0, cv2.BORDER_CONSTANT, value=255)
        value_white_row = len(img[0]) * 255
        array_sign, coord_0, last_sum = [], 0, value_white_row
        for i in range(1, len(img)):
            now_sum = np.sum(img[i])
            if last_sum == value_white_row and now_sum != value_white_row:
                coord_0 = i
            elif last_sum != value_white_row and now_sum == value_white_row:
                if i - coord_0 >= min_space:
                    img_sign = img[coord_0:i]
                    if cut_vertical:
                        img_sign = np.rot90(img_sign)
                    array_sign.append(img_sign)
            last_sum = now_sum
        return array_sign

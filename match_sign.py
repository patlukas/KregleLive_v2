"""Moduł służy do znajdowania jaki znak znajduje się na wycinku obrazu oraz zapisywanie nowego szablonu do systemu."""

import numpy as np
import os
import cv2
from datetime import datetime

from informing import Informing


class _MatchedDetails:
    """
    Klasa do przechowywania informacji o najlepiej przypasowanym znaku.

    data_change(np.ndarray, obj<_SignDetails>, float) funkcja przypisje nowe zmienne do zmiennych obiektu
    self.sign: (None | str) None - nie przypasowano żadnego znaku, str - oznaczenie przypasowanego znaku
    self.matched: (float) wartość z przedziału <0, 1> w jakim stopniu przypasowano znak
    self.on_add_template_to_sign_folder: (func) funkcja dodaje szukany znak do os lub print("") jak nie przypasowano
    self.on_add_template_to_unrecognized_sign_folder: (func) funkcja dodaje znak do folderu z nierozpoznanymi
    """

    def __init__(self, sign_new_template: np.ndarray, add_unrecognized) -> None:
        """
        Funkcja tworzy zmienne obiektu z domyślnymi danymi.

        :param sign_new_template: obraz znaku, dla którego szukane jest dopasowanie
        :param add_unrecognized: funkcja dodająca obraz do folderu z nierozpoznanymi znakami
        """
        self.__sign_new_template = sign_new_template
        self.sign = None
        self.matched = 0
        self.on_add_template_to_sign_folder = lambda: Informing().warning("Nie udało się przypisać znaku!")
        self.on_add_template_to_unrecognized_sign_folder = lambda: add_unrecognized(sign_new_template,
                                                                                    self.sign, self.matched)

    def __str__(self) -> str:
        """Funkcja jest używana przy użyciu print na obiekcie."""
        return f"Przekazany znak został przypasowany do {self.sign} w stopniu {self.matched}"

    def data_change(self, sign_details: object, matched: float) -> None:
        """
        Funkcja zamienia dane obiektu na te przekazane.

        :param sign_details: objekt <_SignDetails> tego znaku który jest aktualnie najbardziej przypasowany
        :param matched: wartość przypasowania znaku z przedziału <0, 1>
        """
        self.sign = sign_details.sign
        self.matched = matched
        self.on_add_template_to_sign_folder = lambda: sign_details.add_new_template(self.__sign_new_template)


class MatchImgToSign:
    """
    Klasa do wykrywania jaka wartość znajduje się na obrazku.

    match_img_to_sign(np.ndarray) -> obj - Funkcja stara się przypasować najbardziej pasujący znak do obrazka
    add_new_temp_to_os(str, np.ndarray) -> bool - funckja dodaje do folderu ze znakami str nowy szablon "np.ndarray"

    list_added_template: (list) <str> lista nazw plików dodanych do systemu podczas działania programu
    """

    def __init__(self, name_main_dir: str = "templates", path_unrecognized: str = "unrecognized",
                 threshold_end_search: float = 0.9) -> None:
        """
        :param name_main_dir: nazwa głównego katalogu
        :param threshold_end_search: wartość przypasowania, po przekroczeniu której kończy się szukanie pasującego znaku
        :param path_unrecognized: nazwa katologu przechowującego nierozpoznane znaki

        Zmienne obiektu:
            :param self.__name_main_dir: (str) przechowuje nazwę głównego katalogu
            :param self.__threshold_end_search: (float) przechowuje wartość z przedziału <0, 1>, funkcja kończy szuaknie
                                                        znaku, po znalezieniu znaku podobnego w tym stopniu
            :param self.__path_unrecognized: (str) ścieżka do folderu z nierozpoznanymi obrazami
            :param self.__list_signs_details: (list) <obj _SignDetails>, przchowuje dane o znakach
                                                     z systemu oraz przechowuje szablony pobrane z systemu
            :param self.list_added_template: (list) <str> lista nazw plików dodanych do systemu
        """
        self.__name_main_dir = name_main_dir
        self.__threshold_end_search = threshold_end_search
        self.__path_unrecognized = path_unrecognized
        self.__list_signs_details = []
        self.list_added_template = []
        self.__create_list_signs()

    def __str__(self) -> str:
        """Funkcja używana przy wywołaniu print na obiekcie klasy, zwraca podstawowe informacje"""
        return f"Obiekt do przypasowywania znaków, {self.__threshold_end_search=}, {self.__name_main_dir=}"

    def __create_list_signs(self) -> None:
        """
        Tworzy strukturę katalogową.

        Jeżeli brakuje jakiegoś katalogu to tworzy go. Dodatkowo dodaje obiekt _SignDetails do każdego znaku i zapisuje
        ten obeikt w self.__list_signs_details
        """
        self.__make_dir(self.__name_main_dir)
        for number_sign in range(10):
            dir_path = f"{self.__name_main_dir}/_ {number_sign} _"
            self.__make_dir(dir_path)
            new_obj = _SignDetails(str(number_sign), self.__resize_img, self.list_added_template, dir_path)
            self.__list_signs_details.append(new_obj)

    @staticmethod
    def __make_dir(path: str) -> bool:
        """
        Jeżeli nie ma katalogu pod podaną ścieżką to tworzy go.

        :param path: ścieżka do katalogu
        :return: True - został stworzony katalog, False - był już taki katalog
        """
        if not os.path.exists(path):
            os.mkdir(path)
            return True
        return False

    def match_img_to_sign(self, img: np.ndarray) -> _MatchedDetails:
        """
        Funkcja służy do odnalezienia najlepszego przypasowania znaku do przekazanego obrazu.

        Najpierw tworzy obiekt który będzie zwracany, zawiera on informacje do jakiego znaku został przypasowany obraz,
        w jakim stopniu są podobne oraz opcję która dodaje znak do systemu.
        Następnie tworzy hierarchię znaków, czyli sprawdza po jednym znaku i ustawie kolejność według dopasowania.
        Następnie sprawdza każdy znak z kolejnych znaków w kolejności jaką ustaliła hierarchia.
        Jeżeli sprawdzony znak jest lepiej przypasowany to zostaje zaaktualizowana zmienna matched_val.
        Jeżeli przypasowanie jest na wyższym poziomie niż self.__threshold_end_search to szukanie kończy się.

        :param img: obraz do przypasowania
        :return: obiekt <_MatchedDetails>
        """
        return_dict = _MatchedDetails(img, self.add_new_unrecognized_temp_to_os)
        for sign_details in self.__get_hierarchy_sign(img):
            for template in sign_details.list_templates:
                matched_val = self.__get_matched_value(img, template)
                if matched_val > return_dict.matched:
                    return_dict.data_change(sign_details, matched_val)
                    if matched_val >= self.__threshold_end_search:
                        return return_dict
        return return_dict

    def __get_hierarchy_sign(self, img: np.ndarray) -> list:
        """
        Funkcja wyznacza kolejność w jakiej mają być sprawdzane znaki.

        Funckja służy do zwrócenia listy sign_details w kolejności jaką ma sprawdzać system.
        Funkcja sprawdza po kolei każde sign_details, jeżeli posiada chociaż jeden znak to sprawdza przypasowanie
        pierwszego szablonu z img i dodaje dict do hierarchy. Następnie sortuje listę hierarchy według przypasowania
        i zwraca listę z obiektami _SignDetails

        :param img: obraz znaku
        :return: lista<_SignDetails> w kolejności do sprawdzenia
        """
        hierarchy = []
        for sign_details in self.__list_signs_details:
            list_templates = sign_details.list_templates
            if list_templates:
                matched_value = self.__get_matched_value(img, list_templates[0])
                if matched_value:
                    hierarchy.append({'sign_details': sign_details, 'matched_value': matched_value})
        hierarchy.sort(key=lambda x: x["matched_value"], reverse=True)
        return [el["sign_details"] for el in hierarchy]

    def __get_matched_value(self, img_to_check: np.ndarray, img_template: np.ndarray) -> float:
        """
        Funkcja zwraca wynik z przedziału <0, 1>, w jakim stopniu obrazki są do siebie podobne.

        Funkja sprawdza jakie jest przypasowanie obrazów i zwraca tą wartość.
        Najpeirw przy użyciu funkcji self.__resize_img ujednolica wielkość obrazów.

        :param img_to_check: obraz który jest przypasowywany
        :param img_template: obraz szablon już zapisany w systemie
        :return: liczba z przedziału <0, 1>, w jakim stopniu obrazy są podobne
        """
        img_to_check = self.__resize_img(img_to_check)[0]
        img_template = self.__resize_img(img_template)[0]
        result = cv2.matchTemplate(img_to_check, img_template, cv2.TM_CCOEFF_NORMED)
        return cv2.minMaxLoc(result)[1]

    @staticmethod
    def __resize_img(img: np.ndarray) -> list:
        """
        Funkcja służy do ujednolicania wielkości obrazów.

        :param img: obraz do przeskalowania.
        :return: lista <np.ndarray, bool> [obraz o wymiarach 30x37, czy wiilkość została zmieniana]
        """
        if len(img) != 37 or len(img[0]) != 30:
            return [cv2.resize(img, (30, 37), interpolation=cv2.INTER_AREA), True]
        return [img, False]

    def add_new_temp_to_os(self, sign: str, img_temp: np.ndarray) -> bool | str:
        """
        Funckja służy do dodania obrazu do systemu.

        Funkcja przeszukuje self.__list_signs_details i jeżeli znajdzie znak "sign" to przypije do niego obraz img_temp

        :param sign: jaki znak znajduje się na obrazie <wartość z przedziału 0, 9>
        :param img_temp: obraz do dodania do systemu
        :return: False - nie udało się dodać znaku, str - ścieżka do dodanego pliku
        """
        for sign_details in self.__list_signs_details:
            if sign_details.sign == sign:
                return sign_details.add_new_template(img_temp)
        Informing().error(f"Znak '{sign}' nie ma swojego _SignDetails w self.__list_signs_details")
        return False

    def add_new_unrecognized_temp_to_os(self, img_temp: np.ndarray, sign: None | str,
                                        matched: float) -> bool |str:
        """
        Metoda dodaje obraz znaku do folderu z nierozpoznanymi znakami.

        Zostaje dodany plik ze znakiem do folderu pod ścieżką self.__path_unrecognized.
        Dodany plik w nazwie będzie miał aktualną datę.

        :param img_temp: obraz nierozpoznanego znaku
        :param sign: jaki znak został oszacowany lub None jak nic nie jest podobne
        :param matched: w jakim stopniu jest podobny
        :return: jeżeli udało się dodać to zwraca ścieżkę do pliku, w innym przypadku False
        """
        new_temp = self.__resize_img(img_temp)[0]
        name_new_file = datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")
        path = f"{self.__path_unrecognized}/{name_new_file}"
        if sign is None:
            path += " UNRECOGNIZED"
        else:
            path += f" {sign}({int(matched*100)}%)"
        try:
            cv2.imwrite(f"{path}.jpg", new_temp)
            np.save(f"{path}.npy", new_temp)
            return f"{path}.npy"
        except FileNotFoundError:
            Informing().error(f"Nie można zapisać pod ścieżką '{path}'")
            return False


class _SignDetails:
    """
    Klasa przechowuje informacje o znakach oraz umożliwia dodanie nowych obrazów znaków do systemu.

    add_new_template(np.ndarray) -> str - funckja dodaje w systemie do folderu z znakami tego typu kolejny szablon

    sign: (str) nazwa znaku, czyli liczba z zakresu <0, 9>
    list_templates: (list) <np.ndarray> każdy element przedstawia jeden obraz szablonu z OS
    """
    def __init__(self, sign: str, on_resize_img, list_added_template: list, dir_path: str) -> None:
        """
        :param sign: oznaczenie znaku (liczba z zakrezu <0, 9>)
        :param on_resize_img: (func) funkcja służąca do ustandaryzowania wielkości obrazów, zwraca (np.ndarray, bool)
                                     gdzie 1. to obraz po zmianie, a 2. to wartość bool czy była zmieniana wielkość
        :param list_added_template: <str> lista nazw dodanych obrazów
        :param dir_path: <str> ścieżka do katalogu przechowującego szablony znaku

        self.sign: (str) przechowuje nazwę znaku
        self.list_templates: (list) <np.ndarray>, każdy element przedstawia jeden obraz szablonu
        self.__path: (str) przechowuje ścieżkę do katalogu ze znakami
        self.__last_index: (int) numer ostatniego szablonu, domyślnie 0
        self.__on_resize_img: (func) funkcja do zmieny wielkośći obrazu
        self.__list_added_template: (list) <str> lista przechowująca nazwy plików dodanych szablonów
        """
        self.sign = sign
        self.list_templates = []
        self.__on_resize_img = on_resize_img
        self.__path = dir_path
        self.__last_index = 0
        self.__list_added_template = list_added_template
        self.__load_sign_from_os()

    def __str__(self) -> str:
        """Funkcja używana przy wywołaniu print na obiekcie klasy, zwraca podstawowe informacje"""
        return f"Obiekt z szablonami do znaku {self.sign}, zawiera {self.__last_index} szablonów. Ścieżka {self.__path}"

    def __load_sign_from_os(self) -> None:
        """
        Funkcja zapisuje w self.list_templates pobrane z systemu szablony.

        Funckja wywołuje self.__get_list_file_name_from_path() w celu otrzymania listy plików z kataogu.
        Następnie każdy obraz znaku umieszcza w self.list_templates.
        Na koniec ustawia self.__last_index jaki numer miał ostatni szablon
        """
        array_name_file = self.__get_list_file_name_from_path()
        for name_file in array_name_file:
            img = np.load(f'{self.__path}/{name_file}')
            img, is_bad_size = self.__on_resize_img(img)
            if is_bad_size:
                Informing().info(f'Szablon "{self.__path}/{name_file}" ma nieodpowiednie wymiary')
            self.list_templates.append(img)
        if array_name_file:
            self.__last_index = int(array_name_file[-1].split(".")[0])

    def __get_list_file_name_from_path(self) -> list:
        """
        Funkcja zwraca posortowaną listę nazw plików z rozszerzeniem ".npy".

        Funckja przegląda folder z ścieżki self.__path oraz wybiera z niego wszystkie pliki kończące się na
        ".npy", następnie sortuje listę znalezionych nazw plików i ją zwraca
        :return: (list<str>) lista nazw plików
        """
        files = os.listdir(self.__path)
        files = [file for file in files if file.endswith(".npy")]
        files.sort()
        return files

    def add_new_template(self, new_temp: np.ndarray) -> bool | str:
        """
        Funkcja dodaje nowy szablon do self.list_templates oraz do systemu operacyjnego.

        Funkcja dodaje przekazany obraz znaku "new_temp" do listy self.list_templates oraz dodaje obraz do folderu.
        Jeden plik z rozszerzeniem ".jpg" przedstawia obraz, a z rozszerzeniem ".npy" przedstawia dokument tekstowy
        Nazwa pliku składa się z pięciu cyfr, jeżeli liczba nie jest 5 cyfrowa to jest uzupełniana na początku 0

        :param new_temp: czarno-biały obraz który jest nowym szablonem
        return: nazwa dodanego pliku lub False jeżeli brakuje katalogu
        """
        new_temp = self.__on_resize_img(new_temp)[0]
        self.list_templates.append(new_temp)
        self.__last_index += 1
        name_new_file = str(self.__last_index)
        while len(name_new_file) < 5:
            name_new_file = "0" + name_new_file
        path = f"{self.__path}/{name_new_file}"
        try:
            cv2.imwrite(f"{path}.jpg", new_temp)
            np.save(f"{path}.npy", new_temp)
            self.__list_added_template.append(f"{path}.npy")
            Informing().warning(f"Dodano nowy szablon znaku '{path}'")
            return f"{path}.npy"
        except FileNotFoundError:
            Informing().error(f"Katalog w ścieżce '{path}' został usunięty")
            return False

# _____ BIBLIOTEKI
import numpy as np
import os
import cv2
import time
from datetime import datetime
from skimage.filters import threshold_local


# _____ ZARZĄDZANIE BŁĘDAMI                                                                                      _____ #

class PrintError:
    """
    Klasa do wyświetlania błędów i zpisywania ich do systemu

    Wymagane biblioteki:
        import numpy as np
        import cv2
        from datetime import datetime
    Funkcje globalne:
        error_message(error_index, error_message, img_sign, img_frame, player_id) - Funkcja odpowiada za pokazanie błędu
            argumenty:
                error_index - (int)  numer błędu
                error_message - (str)  opis błędu
                img_sign - (False/np.ndarray)  jeżeli np.ndarray to obraz znaku w innym przypadku False
                img_frame - (False/np.ndarray)  jeżeli np.ndarray to obraz ramki obrazu z kamery w innym przypadku False
                player_id - (array)  [numer drużyny w której gra gracz, numer zawodnika w drużynie]
    Zmianne globalne:
        list_add_error: (list) lista błędów które wystąpiły podczas działania programu
    Lista błędów:
        101 - MatchImgToSign
    """

    def __init__(self, name_main_dir, list_added_error):
        """
        Funkcja inicjuje klasę, tworzy zmienne w obiekcie:
            :param self.__name_main_dir: (str) nazwa głównego katalogu
            :param self.__name_dir_error: (str) nazwa katalogu w głównym katalogu do przechowywania obrazów błędu
            :param self.__extension_photo_file: (str) rozszerzenie pliku z obrazem
            :param self.list_add_error: (list) globalna lista przechowująca informacje o błędach które wystąpiły

        :param name_main_dir: (str) nazwa głównego katalogu
        :param list_added_error: (list) lista do przechowywania dodanych błędów
        """
        self.__name_main_dir = name_main_dir
        self.__name_dir_error = "error"
        self.__extension_photo_file = ".jpg"
        self.list_add_error = list_added_error

    def error_message(self, error_index=0, error_message="", img_sign=False, img_frame=False, player_id=()):
        """
        Funkcja odpowiada za poinformowanie użytkownka o zaistniałym błędzie i zapisanie informacji w odpowiednim
        katalogu i pliku tekstowym

        :param error_index - (int)  numer błędu
        :param error_message - (str)  opis błędu
        :param img_sign - (False/np.ndarray)  jeżeli np.ndarray to obraz znaku w innym przypadku False
        :param img_frame - (False/np.ndarray)  jeżeli np.ndarray to obraz ramki obrazu z kamery w innym przypadku False
        :param player_id - (array)  [numer drużyny w której gra gracz, numer zawodnika w drużynie]
        """
        player_info = self.__get_player_info(player_id)
        self.__save_error_message_in_file(error_index, error_message, player_info)
        self.__save_error_in_global_errors_list(error_index, error_message, player_info, player_id)
        self.__save_image(img_frame, img_sign, error_index, error_message, player_info)
        self.__print_message(error_index, error_message, player_info)

    @staticmethod
    def __get_player_info(player_id):
        """
        Funckja zwraca  napis inforujący jakiego gracza dotyczy powstały błąd

        :param player_id: (list) lista dwuelementowa
        :return: (str) napis Gi Pj - gdzie i to numer drużyny (1 albo 2), a j to numer gracza (1-6 lub 1-4)
        """
        if len(player_id) != 2:
            return ""
        return f"G{player_id[0]+1} P{player_id[1]+1}"

    @staticmethod
    def __save_error_message_in_file(error_code, error_message, player_info):
        """
        Funckja służy do zapisywania błędu do pliku txt zawieracjącego błędy, dodaje jeszcze informacje o godzinie błędu

        :param error_code: (int) numer błędu
        :param error_message: (str) wiadomość błędu
        :param player_info: (str) informacje jakiego gracza dotyczy błąd
        """
        time_now = datetime.now().strftime("%Y/%m/%d %H-%M-%S-%f")
        file = open("errors.txt", "a")
        file.write(f"{time_now} : \tERROR_{error_code}\t{player_info}\t{error_message} \n")
        file.close()

    def __save_error_in_global_errors_list(self, error_code, error_message, player_info, player_id):
        """
        Funckja zapisuje dane o błędzie w globalnej liście słowników (self.list_add_error)

        :param error_code: (int) numer błędu
        :param error_message: (str) wiadomość błędu
        :param player_info: (str) informacje jakiego gracza dotyczy błąd
        :param player_id: (list) [index drużyny, index gracza w drużynie]
        """
        time_now = datetime.now().strftime("%H:%M:%S")
        error_dict = {
            "time": time_now,
            "error_code": error_code,
            "error_message": error_message,
            "player_info": player_info,
            "player_id": player_id
        }
        self.list_add_error.append(error_dict)

    def __save_image(self, img_frame, img_cell, error_code, error_message, player_info):
        """
        Funkcja zapisuje obrazy z błędami do folderu z obrazami błędów, obrazy zostają zapisane gdy zmienna
        ma typ np.ndarray

        :param img_frame: (np.ndarray/False) obraz z kamery z momentu gdy był błąd
        :param img_cell: (np.ndarray/False) obraz komórki gdzie znaleziono błąd
        :param error_code: (int) numer błędu
        :param error_message: (str) wiadomość błędu
        :param player_info: (str) informacje jakiego gracza dotyczy błąd
        """
        name = f"ERROR_{error_code} {player_info} {error_message}"
        translate = str.maketrans("ąćęłóńśżźĄĆĘŁÓŃŚŻŹ", "acelonszzACELONSZZ")
        name = name.translate(translate)
        time_now = datetime.now().strftime("%Y-%m-%d %H-%M-%S-%f")
        path = f"{self.__name_main_dir}/{self.__name_dir_error}"
        if type(img_cell) == np.ndarray:
            cv2.imwrite(f"{path}/{time_now} {name}.{self.__extension_photo_file}", img_cell)
        if type(img_frame) == np.ndarray:
            cv2.imwrite(f"{path}/{time_now} {error_message}(frame).{self.__extension_photo_file}", img_frame)

    @staticmethod
    def __print_message(error_code, error_message, player_info):
        """
        Funckaj służy do wypisania błędu w konsoli

        :param error_code: (int) numer błędu
        :param error_message: (str) wiadomość błędu
        :param player_info: (str) informacje jakiego gracza dotyczy błąd
        """
        print(f"ERROR_{error_code}\t{player_info}\t{error_message}")


list_add_error = []
print_error = PrintError("main", list_add_error)


# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# _____ KL6     Znajduje najbardziej pasujący znak                                                               _____ #
# -------------------------------------------------------------------------------------------------------------------- #

class MatchImgToSign:
    """
    Wymagane blioteki:
        import numpy as np
        import os
        import cv2
    Wymagane zmienne globalne:
        print_error
    Funkcje globalne:
        match_img_to_sign(img) - funkcja sprawdza jaki znak znajduje się na obrazku "img"
            argumenty:
                img - (np.ndarray) obraz znaku do sprawdzenia
            return:
                obiekt z opcjami:
                    sign: (False, str) jeżeli przypasowano znak to str, inaczej False
                    matched: (float) wartość z przedziału <0, 1> określająca z jaką precyzją przypasowano znak
                    on_add_template: (func) funkcja, jeżeli zostanie wywołana to do systemu zostanie dodany szuakny znak
        add_new_temp_to_os(sign, img) - funckja dodaje do folderu ze znakami "sign" nowy szablon "img",
            argumenty:
                sign: (str) nazwa znaku
                img: (np.ndarray) znak do dodania
            return: (bool) True jeżeli udało się dodać,  False jeżeli takiego folderu nie ma
    Zmianne globalne:
        list_added_template: (list) lista nazw plików dodanych do systemu podczas diząłania programu
    """

    def __init__(self, name_main_dir, list_added_template, threshold_end_search):
        """
        Funkcja inicjuje klasę, tworzy zmienne w obiekcie:
            :param self.__name_main_dir: (str) do przechowywania nazwy głównego katalogu
            :param self.__threshold_end_search: (float) wartość z przedziału <0, 1>, jeżeli uda się znaleźć znak
                                                podobny w tym stopniu do przesłanego obrazu znaku to funkcja szukania
                                                "match_img_to_sign" zostanie przerwana
            :param self.__list_signs_details: (list) lista obiektów self.__SignDetails, przchowuje dane o znakach
                                                z suystemu oraz przechowuje szablony pobrane z systemu
            :param self.list_added_template: (list) lista nazw plików dodanych do systemu podczas diząłania programu

        :param name_main_dir: (str) nazwa głównego katalogu
        :param list_added_template: (list) lista z dodanymi plikami
        :param threshold_end_search: (float) wartość po której przekroczeniu kończy się szukanie pasującego znaku
        """
        self.__name_main_dir = name_main_dir
        self.__threshold_end_search = threshold_end_search
        self.__list_signs_details = []
        self.list_added_template = list_added_template
        self.__create_list_signs()

    class __SignDetails:
        """
        Klasa przechowuje informacje o znakach oraz umożliwia dodanie nowych
        Funckje globalne:
            add_new_template(new_temp) - funckja dodaje w systemie do folderu z znakami tego typu kolejny "new_temp"
                argumenty:
                    new_temp: (np.ndarray) obraz do doania do systemu
                return: (str) nazwę pliku który został dodany
        Zmianne globalne:
            :param self.sign: (str) nazwa znaku
            :param self.list_templates: (list) lista np.ndarray, każdy element przedstawia jeden obraz szablonu z os
        """

        def __init__(self, sign, name_main_dir, on_resize_img, list_added_template):
            """
            Funckja inicjuje klasę, tworzy zmienne:
                :param self.sign: (str) nazwa znaku
                :param self.list_templates: (list) lista np.ndarray, każdy element przedstawia jeden obraz szablonu z os
                :param self.__path: (str) ścieżka do katalogu ze znakami
                :param self.__last_index: (int) numer ostatniego szablonu, domyślnie 0
                :param self.__on_resize_img: (func) funkcja do zmieny wielkośći obrazu
                :param self.__list_added_template: (list) lista przechowująca nazwy plików dodanych szablonów
            Argumenty funkcji:
                :param sign: (int/str) Zapis znaku na klawiaturze
                :param name_main_dir: (str) nazwa katalogu
                :param on_resize_img: (func) funkcja służąca do ustandaryzowania wielkości obrazów, zwraca listę gdzie
                                             pierwszy element jest obrazem o określonym rozmiarze,
                                             a drugi wartością bool czy wielkość obrazu zostałą zmieniona

            Fukcja uruchamia self.__load_sign_from_os() w celu wypełnienia tablicy self.list_templates znakami pobranymi
            z katalogu self.__path oraz ustawaia w zmiennej self.__last_index jaki numer miał ostatni znak
            """
            self.sign = str(sign)
            self.list_templates = []
            self.__on_resize_img = on_resize_img
            self.__path = f"{name_main_dir}/_ {sign} _"
            self.__last_index = 0
            self.__list_added_template = list_added_template
            self.__load_sign_from_os()

        def __load_sign_from_os(self):
            """
            Funckja wywołuje self.__get_list_file_name_from_path() w celu otrzymania listy plików z kataogu.
            Następnie każdy obraz znaku umieszcza w self.list_templates.
            Na koniec ustawia self.__last_index jaki numer miał ostatni szablon
            """
            array_name_file = self.__get_list_file_name_from_path()
            for name_file in array_name_file:
                img = np.load(f'{self.__path}/{name_file}')
                img, is_bad_size = self.__on_resize_img(img)
                if is_bad_size:
                    try:
                        print_error.error_message(101, f'Szablon "{self.__path}/{name_file}" ma nieodpowiednie wymiary')
                    except Exception as ex:
                        print("ERROR 101", ex)
                self.list_templates.append(img)
            if len(array_name_file):
                self.__last_index = int(array_name_file[-1].split(".")[0])

        def __get_list_file_name_from_path(self):
            """
            Funckja przegląda folder z ścieżki self.__path oraz wybiera z niego wszystkie pliki kończące się na
            ".npy", następnie soartuje listę znalezionych nazw plików i ją zwraca
            :return: (list) lista nazw plików
            """
            files = os.listdir(self.__path)
            files = [file for file in files if file.endswith(".npy")]
            files.sort()
            return files

        def add_new_template(self, new_temp):
            """
            Funkcja dodaje przekazany obraz znaku "new_temp" do listy self.list_templates oraz dodaje obraz do folderu,
            jeden plik z rozszerzeniem ".jpg" przedstawia obraz, a z rozszerzeniem ".npy" przedstawia dokument tekstowy

            Nazwa pliku skłąda się z pięciu cyfr, jeżeli liczba nie jest 5 cyfrowa to jest uzupełniana na początku 0

            Argumenty:
                :param new_temp: (np.ndarray) czarno-biały obraz który jest nowym szablonem

            return: (str) nazwa dodanego pliku
            """
            new_temp = self.__on_resize_img(new_temp)[0]
            new_temp = cv2.resize(new_temp, (31, 37), interpolation=cv2.INTER_AREA)
            self.list_templates.append(new_temp)
            self.__last_index += 1
            name_new_file = str(self.__last_index)
            while len(name_new_file) < 5:
                name_new_file = "0" + name_new_file
            path = f"{self.__path}/{name_new_file}"
            cv2.imwrite(f"{path}.jpg", new_temp)
            np.save(f"{path}.npy", new_temp)
            self.__list_added_template.append(f"{path}.npy")
            return f"{path}.npy"

    def __create_list_signs(self):
        """
        Funkcja jest odpowiedzialna stworzenie struktury katalogowej, jeżeli brakuje jakiegoś katalogu,
        oraz stworzenie obiektu self.__SignDetails dla każdego znaku i zapisanie tego obeiktu w zmiennej
        self.__list_signs_details.
        """
        self.__make_dir(self.__name_main_dir)
        for number_sign in range(10):
            path = f"{self.__name_main_dir}/_ {number_sign} _"
            self.__make_dir(path)
            self.__list_signs_details.append(self.__SignDetails(number_sign, self.__name_main_dir,
                                                                self.__resize_img, self.list_added_template))

    @staticmethod
    def __make_dir(path):
        """
        Funkcja tworzy katalog, jeżeli nie istnieje i wtedy zwraca False (nie było takiego katalogu),
        jeżeli istniał to zwraca True

        :param path: (str) ścieżka do katalogu
        :return: (bool)
        """
        if not os.path.exists(path):
            os.mkdir(path)
            return False
        return True

    class __MatchedDetails:
        """
        Klasa do przechowywania informacji o najlepiej przypasowanym znaku
        Funkcje globalne:
            data_change(new_temp, sign_details, matched) funkcja przypisje nowe zmienne do zmiennych obiektu
                Argumenty:
                    new_temp: (np.ndarray) obraz znaku który jest aktualnie przypasowywany
                    sign_details: (obj) obiekt z __SignDetails ze szczegółami danego znaku
                    matched: (float) wartość z przedziału <0, 1> w jakim stopniu przypasowano znak
        Zmienne globalne:
            self.sign: (False/str) False jeżeli nie przypasowano żadnego znaku, str jaki znak przypasowano
            self.matched: (float) wartość z przedziału <0, 1> w jakim stopniu przypasowano znak
            self.on_add_template: (func) funkcja do dodania szukanego znaku do os, lub print("") jeżlei nie przypasowano
        """

        def __init__(self):
            """Funkcja tworzy zmienne obiektu z domyślnymi danymi"""
            self.sign = False
            self.matched = 0
            self.on_add_template = lambda: print("")

        def __str__(self):
            """Funkcja jest używana przy użyciu print na obiekcie"""
            return f"Przekazany znak został przypasowany do {self.sign} w stopniu {self.matched}"

        def data_change(self, new_temp, sign_details, matched):
            """Funkcja zamienia dane obiektu na te przekazane"""
            self.sign = sign_details.sign
            self.matched = matched
            self.on_add_template = lambda: sign_details.add_new_template(new_temp)

    def match_img_to_sign(self, img):
        """
        Funkcja służy do odnalezienia najlepszego przypasowania znaku do przekazanego obrazu.

        Najpierw tworzy obiekt który będzie zwracany, zawiera on informacje do jakiego znaku został przypasowany obraz,
        w jakim stopniu są podobne oraz opcję która dodaje znak do systemu.
        Następnie tworzy hierarchię znaków, czyli sprawdza po jednym znaku i ustawie kolejność według dopasowania.
        Następnie sprawdza każdy znak z kolejnych znakó w kolejności jaką ustaliła hierarchia.
        JEżeli sprawdzony znak jest leipeij przypasowany to zostaje zaaktualizowana zmienna matched_val.
        Jeżeli przypasowanie jest na wyższym poziomie niż  self.__threshold_end_search to szuaknie kończy się.

        :param img: (np.ndarray) obraz do przypasowania
        :return: (obj) obiekt z 3 opcjami:
                        sign: (False/str)
                        matched: (float)
                        on_add_template: (func)
        """
        return_dict = self.__MatchedDetails()
        hierarchy_sign_details = self.__get_hierarchy_sign(img)
        for sign_details in hierarchy_sign_details:
            for template in sign_details.list_templates:
                matched_val = self.__get_matched_value(img, template)
                if matched_val > return_dict.matched:
                    return_dict.data_change(img, sign_details, matched_val)
                    if matched_val >= self.__threshold_end_search:
                        return return_dict
        return return_dict

    def __get_hierarchy_sign(self, img):
        """
        Funckja służy do zwrócenia listy sign_details w kolejności jaką ma sprawdzać system.
        Funkcja sprawdza po kolei każde sign_details, jeżlei posiada chociaż jeden znak to sprawdza przypasowanie
        pierwszego i dodaje dict to hierarchy. Następnie sortuje listę hierarchy weług przypasowania
        i tworzy listę hierarchy_sign_details do której będą przypisane w kolejności do sprawdzenia sign_details.
        Zwracana jest ta lista hierarchy_sign_details

        :param img: (np.ndarray) obraz znaku
        :return: (list) lista obiektów self.__SignDetails w kolejności do sprawdzenia
        """
        hierarchy = []
        for sign_details in self.__list_signs_details:
            list_templates = sign_details.list_templates
            if len(list_templates):
                matched_value = self.__get_matched_value(img, list_templates[0])
                if matched_value > 0:
                    hierarchy.append({'sign_details': sign_details, 'matched_value': matched_value})
        hierarchy.sort(key=lambda x: x["matched_value"], reverse=True)
        hierarchy_sign_details = []
        for el in hierarchy:
            hierarchy_sign_details.append(el["sign_details"])
        return hierarchy_sign_details

    def __get_matched_value(self, img_to_check, img_template):
        """
        Funkja sprawdza jakie jest przypasowanie obrazów i zwraca tą wartość.
        Najpeirw przy użyciu funkcji self.__resize_img ujednolica wielkość obrazów.

        :param img_to_check: (np.ndarray) obraz który jest przypasowywany
        :param img_template: (np.ndarray) obraz szablon już zapisany w systemie
        :return: (float) liczba z przedziału <0, 1>, w jakim stopniu obrazy są przypasowane
        """
        img_to_check = self.__resize_img(img_to_check)[0]
        img_template = self.__resize_img(img_template)[0]
        result = cv2.matchTemplate(img_to_check, img_template, cv2.TM_CCOEFF_NORMED)
        return cv2.minMaxLoc(result)[1]

    @staticmethod
    def __resize_img(img):
        """
        Funkcja służy do ujednolicania wielkości obrazów.

        :param img: (np.ndarray) obraz
        :return: (list) [obraz o wymiarach 30x37, (bool) czy wilekość została zmieniana]
        """
        return_val = [img, False]
        if len(img) != 37 or len(img[0]) != 30:
            return_val = [cv2.resize(img, (30, 37), interpolation=cv2.INTER_AREA), True]
        return return_val

    def add_new_temp_to_os(self, sign, img_temp):
        """
        Funckja służy do dodania obrazu do systemu.
        Funkcja przeszukuje self.__list_signs_details i jeżeli znajdzie znak "sign" to przypije do niego obraz img_temp

        :param sign: (str) jaki znak znajduje się na obrazie
        :param img_temp: (np.ndarray) obraz do dodania do systemu
        :return: (bool) czy udało się dodać obraz (czy istnieje znak "sign")
        """
        for sign_details in self.__list_signs_details:
            if sign_details.sign == sign:
                sign_details.add_new_template(img_temp)
                return True
        return False


# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# _____ KL3     Znalezenienie pasujących wierszy oraz wyznaczneie ich współrzędnych                              _____ #
# -------------------------------------------------------------------------------------------------------------------- #

class LookingForPlayerTables:
    """
    Biblioteki:
        import numpy as np
        import cv2
        from skimage.filters import threshold_local
    Funkcje globalne:
        get_all_option_sequence_columns() - zwraca listę z możliwymi do wyboru rodzajami sekwencji kolumn
            return: (lsit) lista zawierająca listy intów z możliwymi sekwencjami kolumn

        get_list_all_row_data_in_img() - funkcja zwraca listę ze szczegółami dotyczącymi wszystkich komórek na obrazie
            return: (list) lista z obiektami __CellInRow, każdy obiekt zawiera metody:
                            - get_coord_y() - zwraca współrzędną górną i dolną wiersza
                            - get_list_coord_x() - zwraca listę zawierającą listy ze współrzędnymi lewą i prawą
                            - get_coord_x(index) - zwraca współrzędne lewą i prawą kolumny o indeksie "index"

        get_list_row_data() - funkcja zwraca listę ze szczegółami dotyczącymi komórek na obrazie
                                które spełniają wymagania sekwencji
            return: (list) lista z obiektami __CellInRow, każdy obiekt zawiera metody:
                            - get_coord_y() - zwraca współrzędną górną i dolną wiersza
                            - get_list_coord_x() - zwraca listę zawierającą listy ze współrzędnymi lewą i prawą
                            - get_coord_x(index) - zwraca współrzędne lewą i prawą kolumny o indeksie "index"

        set_sequence_columns(sequence_columns) - funckja służy do zmienienia self.__sequence_columns, funkcja ustawia
                                                w self.__sequence_columns wartość przekazaną sequence_columns

        get_row_data(img_frame) - program przeszukuje przekazany obraz w poszukiwaniu wszystkich dostępnych komórek,
                                  które zapisuje w self.__list_all_row_data_in_img, natomiast w self.__list_row_data
                                  zapisuje te komórki, które spełniają założenia self.__sequence_columns
            return: (list) lista z obiektami __CellInRow zawiera informacje o komórkach które spełniają warunki
                           dotyczące szerkości komórek, każdy obiekt zawiera metody:
                            - get_coord_y() - zwraca współrzędną górną i dolną wiersza
                            - get_list_coord_x() - zwraca listę zawierającą listy ze współrzędnymi lewą i prawą
                            - get_coord_x(index) - zwraca współrzędne lewą i prawą kolumny o indeksie "index"
    """
    def __init__(self):
        """
        Funkcja inicjuje klasę, tworzy zmienne w obiekcie:
            :param self.__MAX_SPACE_BETWEEN_COLUMN: (int) maksymalna odległość między wykrytymi komórkami, ta wartość
                                                          jest używana przy sprawdzaniu sekwencji w funkcji
                                                          self.__finding_sequence
            :param self.__THRESHOLD_HORIZONTAL: (int) średnia wartość jaka musi być w wierszu aby uznać ten wiersz
                                                      za koniec/początek wiersza
            :param self.__THRESHOLD_VERTICAL: (int) średnia wartość jaka musi być w kolumnie aby uznać tą kolumnę
                                                    za koniec/początek kolumny w wierszu
            :param self.__MIN_WIDTH: (int) minimalna szerokość jaką musi mieć komórka aby dodać ją do listy
            :param self.__MIN_HEIGHT: (int) minimalna wysokość jaką musi mieć wiersz aby dodać go do listy
            :param self.__sequence_columns: (list) lista sekwencji szerokości kolumn w wierszu, zawiera liczby całkowite
                                                   zaczynając od 0, liczba 0 oznacza że kolumna jest najwęższa, a
                                                   każdy element o tym samym numerze musi mieć zbliżoną szerokość
                                                   i mieć mniejszą/większą szerokość niż
                                                   kolumna o numerze mniejszym/więkzym
            :param self.__list_all_row_data_in_img: (list)lista obiektów __CellInRow zawiera wszyskie wykryte komórki
            :param self.__list_row_data: (list) lista obiektów __CellInRow zawiera komórki spełniające warunki sekwencji
        """
        self.__MAX_SPACE_BETWEEN_COLUMN = 8
        self.__THRESHOLD_HORIZONTAL = 150
        self.__THRESHOLD_VERTICAL = 20
        self.__MIN_WIDTH = 15
        self.__MIN_HEIGHT = 10
        self.__sequence_columns = [0, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.__list_all_row_data_in_img = []
        self.__list_row_data = []

    class __CellInRow:
        """
        Klasa służy do przechowywania informacji o współrzędnych wierszy jakie zosatły wykryte
        oraz o komórkach w tym wierszu

        Funkcje globalne:
            get_coord_y() - zwraca górną i dolną współrzędną wiersza
            get_list_coord_x() - zwraca listę, w której każdy eleement odpowiada jednej komórce w wierszu
                                 i zawiera prawą i lewą współrzędną
            get_coord_x(index) - zwraca prawą i lewą współrzędną komórki o indeksie "index"
                                 lub False gdy index jest zbyt duży
        """

        def __init__(self, coord_y, array_coord_x):
            """
            Funkcja inicjuje klasę, tworzy zmienne w obiekcie:
                self.__coord_y: (list) lista dwóch liczb całkowitych określającą górną i dolną granicę wiersza
                self.__array_coord_x: (list) lista list dwóch liczb całkowitych określającą lewą i prawą
                                              granicę komórki w wierszu

            :param coord_y: (list) pod indeksem 0 przechowuje y0, a pod indeksem 1 przechowuje y1
            :param array_coord_x: (list) tablica przechowuje tablice, w których pod 0 indeksem jest x0, a pod 1 x1
            """
            self.__coord_y = coord_y
            self.__array_coord_x = array_coord_x

        def get_coord_y(self):
            """:return: zwraca y0 y1"""
            return self.__coord_y[0], self.__coord_y[1]

        def get_list_coord_x(self):
            """
            Funkcja zwraca listę, w której każdy eleement odpowiada jednej komórce w wierszu i zawiera
            prawą i lewą współrzędną danej komórki
            """
            return self.__array_coord_x

        def get_coord_x(self, index_coord_x):
            """
            Funkcja zwraca x0, x1 z kolumny o indeksie 'index_coord_x'
            :param index_coord_x: (int) indeks kolumny
            :return: (list/False) zwraca x0 x1 lub False jeżeli jest podany za duży index
            """
            if index_coord_x >= len(self.__array_coord_x):
                return False
            return self.__array_coord_x[index_coord_x][0], self.__array_coord_x[index_coord_x][1]

    @staticmethod
    def get_all_option_sequence_columns():
        """Funkcja zwraca listę z możliwymi sekqencji kolumn do wyboru"""
        return [
            [0, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]

    def get_list_all_row_data_in_img(self):
        """
        funkcja zwraca listę ze szczegółami dotyczącymi wszystkich komórek na obrazie
        return: (list) lista z obiektami __CellInRow, każdy obiekt zawiera metody:
                        - get_coord_y() - zwraca współrzędną górną i dolną wiersza
                        - get_list_coord_x() - zwraca listę zawierającą listy ze współrzędnymi lewą i prawą
                        - get_coord_x(index) - zwraca współrzędne lewą i prawą kolumny o indeksie "index"
        """
        return self.__list_all_row_data_in_img

    def get_list_row_data(self):
        """
        Funkcja zwraca listę ze szczegółami dotyczącymi komórek na obrazie które spełniają wymagania sekwencji
        return: (list) lista z obiektami __CellInRow, każdy obiekt zawiera metody:
                        - get_coord_y() - zwraca współrzędną górną i dolną wiersza
                        - get_list_coord_x() - zwraca listę zawierającą listy ze współrzędnymi lewą i prawą
                        - get_coord_x(index) - zwraca współrzędne lewą i prawą kolumny o indeksie "index"
        """
        return self.__list_row_data

    def set_sequence_columns(self, sequence_columns):
        """
        funckja służy do zmienienia self.__sequence_columns, funkcja ustawia w self.__sequence_columns
        na wartość przekazaną sequence_columns
        """
        self.__sequence_columns = sequence_columns

    def get_row_data(self, img_frame):
        """
        Funkcja przeszukuje przekazany obraz w poszukiwaniu wszystkich dostępnych komórek, które zapisuje
        w self.__list_all_row_data_in_img, natomiast w self.__list_row_data zapisuje te komórki, które spełniają
        założenia self.__sequence_columns

        :params img_frame: (np.ndarray) kolorowy obraz z kamery

        return: (list) lista z obiektami __CellInRow zawiera informacje o komórkach które spełniają warunki
                       dotyczące szerkości komórek, każdy obiekt zawiera metody:
                        - get_coord_y() - zwraca współrzędną górną i dolną wiersza
                        - get_list_coord_x() - zwraca listę zawierającą listy ze współrzędnymi lewą i prawą
                        - get_coord_x(index) - zwraca współrzędne lewą i prawą kolumny o indeksie "index"
        """
        self.__list_all_row_data_in_img = []
        self.__list_row_data = []
        if type(img_frame) != np.ndarray:
            return self.__list_row_data

        img_frame_black = self.__to_black_image(img_frame)
        array_coord_y = self.__looking_for_row(img_frame_black)

        for coord_y in array_coord_y:
            y0, y1 = coord_y
            img_row_black = img_frame_black[y0:y1]
            array_coord_x = self.__looking_for_column(img_row_black)
            array_coord_x_after_check_sequence = self.__finding_sequence(array_coord_x)

            if array_coord_x_after_check_sequence:
                self.__list_row_data.append(self.__CellInRow(coord_y, array_coord_x_after_check_sequence))
            self.__list_all_row_data_in_img.append(self.__CellInRow(coord_y, array_coord_x))

        return self.__list_row_data

    def __looking_for_row(self, img_frame_black):
        """
        Funkcja służy do pośredniczenia między wywołaniem w poszukiwaniu wierszy a self.__create_coord_array.

        :param img_frame_black: (np.ndarray) czarno-biały obrazy z kamery
        :return: (list) lista list dwuelementowych zawierających górne i dolne współrzędne znalezionych wierszy
        """
        return self.__create_coord_array(img_frame_black, self.__MIN_HEIGHT,
                                         self.__THRESHOLD_HORIZONTAL, looking_row=True)

    def __looking_for_column(self, img_frame_black):
        """
        Funkcja służy do pośredniczenia między wywołaniem w poszukiwaniu komórek w wierszu  a self.__create_coord_array.

        :param img_frame_black: (np.ndarray) czarno-biały obrazy z kamery
        :return: (list) lista list dwuelementowych zawierających lewe i prawe współrzędne znalezionych komórek w wierszu
        """
        return self.__create_coord_array(img_frame_black, self.__MIN_WIDTH,
                                         self.__THRESHOLD_VERTICAL, looking_row=False)

    @staticmethod
    def __to_black_image(img):
        """
        Funkcja zamienia obraz na czarno-biały. Jeżeli obraz jest kolorowy (ma 3 wymiary) jest zamieniany na obraz szary
        jeżeli nie to odrazu jest zamieniany na czarno-biały

        :param img: (np.ndarray) kolorowy lub szary obraz obraz
        :return: (np.ndarray) zwraca czarno-biały obraz
        """
        if len(img.shape) == 3:
            img = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2GRAY)
        t_val = threshold_local(image=img, block_size=17, offset=10, method='gaussian')
        img = (img > t_val).astype('uint8') * 255
        return img

    @staticmethod
    def __create_coord_array(img, min_space, threshold, looking_row):
        """
        Funkcja ma za zadanie zwrócenie tablicy z współrzędnymi
            - y0 y1 przy looking_row==True
            - x0 x1 przy looking_row==False

        Jeżeli looking_row==False to obraz jest okręcany o 270 stopni,
        aby pierwsza kolumna odpowiadała po przekształceniu pierwszemu wierszowi

        Tablica array_all_wsp przechowuje współrzędne wszystkich wierszy,
        których średnia wartość jest większa niż threshold

        Tablica array_coord, czyli ta która jest zwracana, przechowuje współrzędne zaczynające i kończące sekwencję
        kolejnych współrzędnych z array_all_wsp, ale różnica między początkiem a końcem musi być >= minSpace

        :param img: (np.ndarray) czarno-biały obraz
        :param threshold: (int) próg średniej, jeżeli średnia wartość przekroczy tą granicę
                                to współrzędna jest zapisywana w tablicy do array_all_wsp
        :param looking_row: (bool) zmienna określa czy sprawdzane są wiersze(True) czy kolumny(False)
        :param min_space: (int) ta zmienna określa minimalną odległość między wsp0 a wsp1
        :return: zwraca tablicę tablic, gdzie pod 0 indeksem jest początkowa współrzędna, pod indeksem 1 końcowa
        """
        img = img.copy()
        if not looking_row:
            img = np.rot90(img, 3)

        array_all_coord = []
        for coord in range(len(img)):
            line = img[coord]
            suma = np.sum(line)
            if suma > threshold * len(line):
                array_all_coord.append(coord)

        array_coord = []
        len_array = len(array_all_coord)
        coord_0 = 0
        for i in range(len_array):
            coord_now = array_all_coord[i]
            if i == 0 or array_all_coord[i - 1] < coord_now - 1:
                coord_0 = coord_now
            if i == len_array - 1 or array_all_coord[i + 1] > coord_now + 1:
                if coord_now - coord_0 >= min_space:
                    array_coord.append([coord_0, coord_now + 1])
        return array_coord

    def __finding_sequence(self, array_coord_x):
        """
        Funkcja szukająca sekwencji współrzędnych coord_x, których szerokość spełnia sequenceColumns

        Najierw sprawdza czy jest wystarcająca ilość kolumn, aby dało się znaleźć sekwencję.
        Następnie sprawdza każdą możliwą sekwencję do znalezienia pasującej:
            Sprawdza czy sekwencja jest spełniona, a następnie czy zapisane szerokości są rosnące,
            jeżeli tak to zwraca znalezioną sekwencję
        Jeżeli nie udało się znaleźć to zwraca False

        :param array_coord_x: (array) tablica tablic [x0, x1]
        :return: tablicę tablic [x0, x1], których współrzędne spełniają założenia sequence_columns
                 False jeżeli nie udało się znaleźć sekwencji
        """
        len_sequence = len(self.__sequence_columns)
        how_many_column = len(array_coord_x)
        if how_many_column < len_sequence:
            return False

        for firstX in range(how_many_column - len_sequence):
            array_width = np.full(max(self.__sequence_columns) + 1, -1)
            is_matched = True
            for nr_sequence in range(len_sequence):
                index_width = self.__sequence_columns[nr_sequence]
                if index_width == -1:
                    continue
                x0, x1 = array_coord_x[firstX + nr_sequence]
                cell_width = x1 - x0
                expected_width = array_width[index_width]
                if expected_width == -1:
                    array_width[index_width] = cell_width
                    continue
                if expected_width * 0.9 > cell_width or expected_width * 1.1 < cell_width:
                    is_matched = False
                    break
            width_is_growing = True
            cell_next_to_the_cell = True
            for x in range(len(array_width) - 1):
                if array_width[x] >= array_width[x + 1]:
                    width_is_growing = False
                    break
                if array_coord_x[firstX + x][1] + self.__MAX_SPACE_BETWEEN_COLUMN < array_coord_x[firstX + 1 + x][0]:
                    cell_next_to_the_cell = False
            if is_matched and width_is_growing and cell_next_to_the_cell:
                return array_coord_x[firstX:firstX + len_sequence]
        return False


tt = []
pe = PrintError("main", tt)
t = []
t1 = time.time()
k = LookingForPlayerTables()
t2 = time.time()

s = cv2.imread("main/b.png")
s = cv2.resize(s, (1080, 720), interpolation=cv2.INTER_AREA)

t3 = time.time()
# xx = k.get_row_data(s)
t4 = time.time()
print(t2 - t1, t3 - t2, t4 - t3)
xx = k.get_list_all_row_data_in_img()
for y in xx:
    yy0, yy1 = y.get_coord_y()
    for xx0, xx1 in y.get_list_coord_x():
        cv2.rectangle(s, (xx0, yy0), (xx1, yy1), (0, 0, 255), 1)
cv2.imshow("L", s)
cv2.waitKey(0)

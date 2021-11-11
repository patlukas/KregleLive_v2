# _____ BIBLIOTEKI
import numpy as np
import os
import cv2
import time
from datetime import datetime
from skimage.filters import threshold_local
import copy


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



# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# _____ KL3     Znalezenienie pasujących wierszy oraz wyznaczneie ich współrzędnych                              _____ #
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# _____ KL2     Tworzenie tablicy z obiektami do zbierania danych o graczach                                     _____ #
# -------------------------------------------------------------------------------------------------------------------- #




# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# _____ KL10     Sprawdzenie czy tablica z wynikami została przesunięta                                          _____ #
# -------------------------------------------------------------------------------------------------------------------- #

# def get_array_img_cell_name(img, list_group, index_column):
#     """
#     Funkcja zwraca tablicę z wyciętymi komórkami z nazwami pierwszych graczy z drużyn. Potem te wycinki służą do
#     sprawdzneia czy obraz został przesunięty
#     :param img: (np.ndarray) obraz
#     :param list_group: (array) tablica zawierająca informacje o graczach i współrzędne komórek
#     :param index_column: (int) w której kolumnie znajdują się nazwy graczy
#     :return: (array) tablicę obrazów z wyciętymi komórkami
#     """
#     array_img_cell_name = []
#     for group in list_group:
#         img_cell_name = group[0].get_cell(index_column, img)
#         array_img_cell_name.append(img_cell_name)
#     return array_img_cell_name
#
#
# def check_window_layout(img, array_img_cell_name, list_group, index_column):
#     """
#     Funkcja sprawdza czy tablice z wynikami zostały przesunięte
#     :param img: (np.ndarray) obraz
#     :param array_img_cell_name: (array) tablica z zapisanymi już wyciętymi komórkami
#                                 (None) jeżeli jeszcze nie jest zapisana taka tablica
#     :param list_group: (array) tablica z informacjami o graczach
#     :param index_column: (int) numer kolumny zawierającej nazwy graczy
#     :return: (bool) czy trzeba od nowa znaleźć współrzędne komórek
#     """
#     if array_img_cell_name is None:
#         return True
#     new_array_img_cell_name = get_array_img_cell_name(img, list_group, index_column)
#     for i in range(len(list_group)):
#         img1, img2 = array_img_cell_name[i], new_array_img_cell_name[i]
#         if img1.shape != img2.shape:
#             return True
#         if len(img1) != len(img2) or len(img1[0]) != len(img2[0]):
#             return True
#         result = cv2.matchTemplate(img2, img1, cv2.TM_CCOEFF_NORMED)
#         if cv2.minMaxLoc(result)[1] < 0.95:
#             return True
#     return False
#
#
# class CheckWindowLayout:
#     def __inti__(self):
#         self.__array_img_cell_name = []
#         self.
#
#     def __get_array_img_cell_name(self, how_many_group, ):
#         array_img_cell_name = []
#         for group in list_group:
#             img_cell_name = group[0].get_cell(index_column, img)
#             array_img_cell_name.append(img_cell_name)
#         return array_img_cell_name
#

# TODO 1 - klasa do przechowywania wyników graczy oraz wsp komórek, jeżeli 2 drużyny to liczy ligowe pojedynki
# TODO 2 - klasa srawdzająca czy tabelka zostałą przesunięta
# TODO 3 - klasa odczytująca wyniki


# k.on_data_initialization(2, 6)
# k.teams[0][1].update_data(number_of_rzut_in_tor=16, result_in_last_rzut=4)
# k.teams[0][1].update_data(number_of_rzut_in_tor=15, result_in_last_rzut=4)
# k.teams[0][1].update_data(number_of_rzut_in_tor=30, result_in_last_rzut=2)
# k.teams[0][1].update_data(number_of_rzut_in_tor=0, result_in_last_rzut=0)
# k.teams[0][1].update_data(number_of_rzut_in_tor=2, result_in_last_rzut=4)
# k.teams[0][1].update_data(number_of_rzut_in_tor=3, result_in_last_rzut=6)
# k.teams[0][1].update_data(number_of_rzut_in_tor=4, result_in_last_rzut=0)
# k.teams[0][1].update_data(number_of_rzut_in_tor=5, result_in_last_rzut=7)
# k.teams[0][1].update_data(number_of_rzut_in_tor=7, result_in_last_rzut=14)
# print(k.teams[0][1])

tt = []

t = []




# xx = k.get_list_all_row_data_in_img()

# for y in xx:
#     yy0, yy1 = y.get_coord_y()
#     for xx0, xx1 in y.get_list_coord_x():
#         cv2.rectangle(s, (xx0, yy0), (xx1, yy1), (0, 0, 255), 1)
# cv2.imshow("L", s)
# cv2.waitKey(0)

pe = PrintError("main", tt)

class Main:
    def __init__(self):
        self.__webcam_frame = None
        self.__obj_to_looking_cell = LookingForPlayerTables()
        self.__obj_to_storage_player_results = StorageOfAllPlayersScore()
        self.__obj_to_match_img_to_sign = MatchImgToSign("main", 0.9)
        self.__list_coord_cell = None
        self.__obj_to_storage_player_results.on_data_initialization(2, 6)
        self.__get_webcam_frame()
        self.__looking_coord_cell()
        self.__start()

        x = self.__obj_to_storage_player_results.teams[0][0].get_cell(6, self.__webcam_frame)
        print(self.__obj_to_match_img_to_sign.match_img_to_sign(x))
        # cv2.imshow("L", x)
        # cv2.waitKey(10000)

    def __get_webcam_frame(self):
        s = cv2.imread("main/b.png")
        s = cv2.resize(s, (1080, 720), interpolation=cv2.INTER_AREA)
        self.__webcam_frame = s

    def __looking_coord_cell(self):
        self.__list_coord_cell = self.__obj_to_looking_cell.get_row_data(self.__webcam_frame)

    def __start(self):
        where_players_belong = (
            {"group": 0, "index": 0},
            {"group": 0, "index": 1},
            {"group": -1, "index": -1},
            {"group": 0, "index": 2},
            {"group": 0, "index": 3},
            {"group": -1, "index": -1},
            {"group": 1, "index": 0},
            {"group": 1, "index": 1},
            {"group": -1, "index": -1},
            {"group": 1, "index": 2},
            {"group": 1, "index": 3},
            {"group": -1, "index": -1}
        )
        if len(where_players_belong) != len(self.__list_coord_cell):
            print("K")
            return
        for i, details in enumerate(where_players_belong):
            g, p = details["group"], details["index"]
            if g == -1 or p == -1:
                continue
            print(self.__list_coord_cell)
            self.__obj_to_storage_player_results.teams[g][p].update_coord_cell(self.__list_coord_cell[i])

Main()
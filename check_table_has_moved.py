"Moduł odpowiada za wykrywanie przesunięcia tablicy z wynikami."

from search_players_rows import _CellInRow
import cv2
import numpy as np
from typing import Union


class CheckTableHasMoved:
    """
    Klasa do sprawdzania, czy tablice z wynikami drużyn zostały przesunięte.

    Kolejność sprawdzania:
        klasa sprawdza czy w miejscu w którym ma być nazwa gracza (prawdopodobnie kolumna o indexie 1)
        znajduje się doklądnie to samo co jest zapisane w pamięci obiektu. Jeżeli wartości się róźnią
        to zostaje zwrócony False.

        W zamyśle po zwróceniu przez obiekt wartości False (zmienił się układ) funkcja wywołująca metodę
        pwinna wykryć ponownie komórki na obrazie i wywołać funkcję w tym obiekcie, aby zaaktualizować listę
        listę wyciętych komórk, które są potrzebne do sprawdzania.

        check_table_has_moved(np.ndarrau) -> bool - funckja sprawdza czy wycięte komórki są nadal takie same
                                                    True - okno się przesunęło, False - wszystko jest tak samo
        update_cells_after_generate_rows_details(np.ndarray, list[_CellInRow], int) -> None - funckja aktualizuje dane
                                                                                oraz generuje listę wyciętych komórek
    """

    def __init__(self):
        """
        __list_cutted_cells: lista z wyciętymi komórkami, służącymi za wzór
        __index_column: numer kolumny z której pochodzą komórki
        __list_row_details: lista z danymi o każdym wierszu
        """
        self.__list_cutted_cells: list[np.ndarray] = []
        self.__index_column: int = 1
        self.__list_row_details: list[_CellInRow] = []

    def check_table_has_moved(self, img: np.ndarray) -> bool:
        """
        Funkcja jest odpowiedzialna za sprawdzenie, czy tabelki zmieniły swoje położenie.

        Dokładniej: czy w każdym wierszu w komórkach w kolumnie o indeksie self.__index_column w klatce img jest ten sam
        obraz co zapisany został zapisany w self.__list_cutted_cells.

        :param img: obraz klatki
        :return: True jeżeli obraz się przesunął lub lista jest pusta
        """
        if len(self.__list_row_details) != len(self.__list_cutted_cells):
            return True
        if len(self.__list_row_details) == 0:
            print("Lista z szczegółami o wierszach jest pusta")
            return True
        for i, row_details in enumerate(self.__list_row_details):
            img_to_check = row_details.get_cell(img, self.__index_column)
            result = cv2.matchTemplate(img_to_check, self.__list_cutted_cells[i], cv2.TM_CCOEFF_NORMED)
            print(cv2.minMaxLoc(result)[1])
            if cv2.minMaxLoc(result)[1] < 0.95:
                return True
        return False

    def update_cells_after_generate_rows_details(self, img: np.ndarray,
                                                 list_row_details: list[_CellInRow], index_column: int) -> None:
        """
        Funkcja służy do inicjowania nowej tablicy z wyciętymi komórkami.

        Po wygenerownaiu nowej tablicy list_row_details należy wywołać tą metodę, aby zaaktualizować
        self.__list_row_details, self.__index_column oraz wygenerować self.__list_cutted_cells.

        :param img: obraz klatki z której zostaną wycięte komórki
        :param list_row_details: lista z współrzędnymi komórek na obrazie
        :param index_column: numer kolumny z której mają być wycięte komórki, powinna być to komórka z nazwami graczy
        """
        self.__index_column = index_column
        self.__list_cutted_cells = []
        self.__list_row_details = list_row_details
        for row_details in list_row_details:
            self.__list_cutted_cells.append(row_details.get_cell(img, index_column))

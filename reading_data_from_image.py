"""
Moduł odpowiedzialny za odczyt aktualnych danych z obrazu, dokładniej informacji o numerze toru, rzutu i wyniku.
"""
import numpy as np
from search_players_rows import _CellInRow
from reading_numbers_from_cell import ReadingNumbersFromCell
from typing import Union, Tuple


class ReadingDataFromImage:
    """
    Klasa służy do odczytu aktualnych danych z podanego numeru wiersza.
    """
    def __init__(self, obj_to_read_number_from_cell: ReadingNumbersFromCell,
                 column_with_lane: int, column_with_throws: int, column_with_result):
        self.__obj_to_read_number_from_cell = obj_to_read_number_from_cell
        self.__column_with_lane: int = column_with_lane
        self.__column_with_throw: int = column_with_throws
        self.__column_with_result: int = column_with_result
        self.__list_row_data: list[_CellInRow] = []

    def update_indexes_of_columns(self, column_with_lane: int, column_with_throws: int, column_with_result) -> None:
        """
        Metoda aktualizuje numery kolumn w których znajdują się określone informacje.

        :param column_with_lane: numer kolumn w której znajduje się numer toru na którym zawodnik gra
        :param column_with_throws: numer kolumn w której znajduje się numer rzutu zawodników na torach
        :param column_with_result: numer kolumny z wynikami graczy
        """
        self.__column_with_lane = column_with_lane
        self.__column_with_throw = column_with_throws
        self.__column_with_result = column_with_result

    def update_list_row_data(self, new_list_row_data: list[_CellInRow]) -> None:
        """
        Metoda aktualizuje listę ze informacjami o poszczególnych wierszach.

        :param new_list_row_data: lista z obiektami _CellInRow, zaiwerającymi szczegółowe informacje o wierszach
        """
        self.__list_row_data = new_list_row_data

    def read_data_from_row(self, img: np.ndarray,
                           index_of_row: int) -> tuple[Union[int, None], Union[int, None], Union[int, None]]:

        """
        Moduł służący do oczytu danych znajduących się w 3 kolumnach u gracza który ma swoje dane w podanym wierszu.

        :param img: obraz(klatka) z tabelami do odczytu
        :param index_of_row: numer wiersza z którego mają być odczytane dane
        :return: zwraca trzy odczytane wartości, każda z tych wartości może być int lub None
        """
        if len(self.__list_row_data) <= index_of_row:
            raise ValueError(f"Lista __list_row_data zawiera za mało wierszy, bo tylko {len(__list_row_data)}, "
                             f"a potrzeby jest wiersz o indeksie {index_of_row}")

        lane_cell = self.__list_row_data[index_of_row].get_cell(img, self.__column_with_lane)
        throw_cell = self.__list_row_data[index_of_row].get_cell(img, self.__column_with_throw)
        result_cell = self.__list_row_data[index_of_row].get_cell(img, self.__column_with_result)

        lane = self.__obj_to_read_number_from_cell.read_number_from_one_digit_cell(lane_cell)
        throw = self.__obj_to_read_number_from_cell.read_number_from_three_digits_cell(throw_cell)
        result = self.__obj_to_read_number_from_cell.read_number_from_three_digits_cell(result_cell)

        return lane, throw, result

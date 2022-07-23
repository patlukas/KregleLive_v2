"""Moduł odpowiedzialny za znajdowanie na obrazku sekwencji współrzędnych komórek"""

import numpy as np
import cv2
from skimage.filters import threshold_local

from informing import Informing


class _CellInRow:
    """
    Klasa służy do przechowywania informacji o współrzędnych wierszy oraz komórkach w wierszu, które zostały wykryte.

    get_coord_y() -> list<int, int> - zwraca górną i dolną współrzędną wiersza
    get_list_coord_x() -> list<list<int, int>> zwraca listę dwuelementowych list z współrzędnymi: lewą i prawą komórki
    get_coord_x(int) -> list<int, int> - zwraca prawą i lewą współrzędną komórki o indeksie "index"
    get_cell(np.ndarray, int) -> np.ndarray - zwraca wyciętą komórkę z kolumny o podanym indeksie
    """
    def __init__(self, coord_y: list, array_coord_x: list) -> None:
        """
        :param coord_y: list<int, int> pod indeksem 0 przechowuje y0, a pod indeksem 1 przechowuje y1
        :param array_coord_x: list<list<int, int>>  w których pod 0. indeksem jest x0, a pod 1. x1

        __coord_y: (list<int, int>) lista dwóch liczb całkowitych określającą górną i dolną granicę wiersza
        __array_coord_x: (list<list<int, int>>) lista dwuelementowych list z lewą i prawą granicę komórki w wierszu
        """
        self.__coord_y = coord_y
        self.__array_coord_x = array_coord_x

    def __repr__(self) -> str:
        """Funkcja jest używana przy użyciu print na obiekcie"""
        return f"{self.__coord_y=} {self.__array_coord_x=}"

    def get_coord_y(self) -> list:
        """
        Funkcja zwraca górną i dolną współrzędną wiersza.

        :return: list<int, int> gdzie pierwszy int to górna współrzędna, a druga to dolna współrzędna
        """
        return self.__coord_y

    def get_list_coord_x(self) -> list:
        """
        Funkcja zwraca listę, gdzie każdy element odpowiada jednej komórce i jest reprezentowany przez list<int, int>,
        gdzie każda zawiera lewą i prawą współrzędną komórki.

        :return: list<list<int, int>>
        """
        return self.__array_coord_x

    def get_coord_x(self, index_coord_x: int) -> list:
        """
        Funkcja zwraca lewą i prawą współrzędną kolumny o indeksie 'index_coord_x'.

        :param index_coord_x: indeks kolumny
        :return: (list) zwraca x0 x1
        """
        if index_coord_x >= len(self.__array_coord_x):
            raise IndexError
        return self.__array_coord_x[index_coord_x]

    def get_cell(self, img: np.ndarray, index_column: int) -> np.ndarray:
        """
        Funkcja zwraca wciętą komórkę z wybranej kolumny.

        :param index_column: index kolumny
        :param img: obraz z którego będzie wycinana komórka
        :return: obraz komórki
        """
        y0, y1 = self.get_coord_y()
        x0, x1 = self.get_coord_x(index_column)
        if len(img) <= y1 or len(img[0]) <= x1:
            raise IndexError("Image is too small")
        else:
            return img[y0:y1, x0:x1]


class LookingForPlayerTables:
    """
    Klasa służy do wyznaczenia współrzędnych komórek na obrazie.

    get_list_possible_sequence_names() -> list<str> - zwraca listę z możliwymi do wyboru rodzajami sekwencji kolumn
    get_list_all_row_data_in_img() -> list<_CellInRow> - zwraca listę ze szczegółami dotyczącymi WSZYSTKICH komórek
    get_list_row_data() -> list<_CellInRow> - zwraca listę ze szczegółami dotyczącymi komórek zgodnych z sekwencją
    set_sequence_columns(list<list<int>>) -> None - funckja zmienienia self.__sequence_columns
    get_row_data(np.ndarray) -> list<_CellInRow> - wyszukuje komórek na obrazie i zwraca to samo co get_list_row_data()
    drawing_cells_in_image(np.ndarray) -> np.ndarray - rysuje komórki spełniające warunki sekwencji na obrazie
    drawing_all_cells_in_image(np.ndarray) -> np.ndarray - rysuje wszystkie wykryte komórki na obrazie
    """
    def __init__(self, obj_to_reading_data_from_image) -> None:
        """
        __MAX_SPACE_BETWEEN_COLUMN: (int) maksymalna odległość między wykrytymi komórkami, ta wartość jest używana przy
                                   sprawdzaniu sekwencji w funkcji self.__finding_sequence
        __THRESHOLD_HORIZONTAL: (int) średnia wartość (*1) jaka musi być w wierszu uznać go za koniec/początek wiersza
        __THRESHOLD_VERTICAL: (int) średnia wartość (*1) w kolumnie aby uznać ją za koniec/początek kolumny w wierszu
        __MIN_WIDTH: (int) minimalna szerokość jaką musi mieć komórka aby dodać ją do listy
        __MIN_HEIGHT: (int) minimalna wysokość jaką musi mieć wiersz aby dodać go do listy
        __sequence_columns: (list) lista sekwencji szerokości kolumn w wierszu, zawiera liczby całkowite zaczynając od 0
                           liczba 0 oznacza że kolumna jest najwęższa, a każdy element o tym samym numerze musi  mieć
                           zbliżoną szerokość i mieć mniejszą/większą szerokość niż kolumna o numerze mniejszym/więkzym
        __list_all_row_data_in_img: (list<_CellInRow>) zawiera wszyskie wykryte komórki
        __list_row_data: (list<_CellInRow>) zawiera komórki spełniające warunki sekwencji
        __obj_to_reading_data_from_image: ReadingDataFromImage - obiekt do odczytu danych z obrazu, tutaj ustawia
                                                                 się mu kolumny
        (*1) średnia wartość, czyli średnia wartość pikseli w monochromatychnym obrazie gdzie 255 to biały a 0 to czarny
        """
        self.__MAX_SPACE_BETWEEN_COLUMN = 8
        self.__THRESHOLD_HORIZONTAL = 150
        self.__THRESHOLD_VERTICAL = 50
        self.__MIN_WIDTH = 15
        self.__MIN_HEIGHT = 10
        self.__sequence_columns = [0, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.__list_all_row_data_in_img = []
        self.__list_row_data = []
        self.__obj_to_reading_data_from_image = obj_to_reading_data_from_image
        self.set_sequence_columns(self.get_list_possible_sequence_names()[0])

    def get_list_all_row_data_in_img(self) -> list:
        """
        Funkcja zwraca listę ze szczegółami dotyczącymi WSZYSTKICH wykrtych komórek na obrazie.

        return: list<_CellInRow> zawiera informacje o WSZYSTKICH wykrytych komórkach
        """
        return self.__list_all_row_data_in_img

    def get_list_row_data(self) -> list:
        """
        Funkcja zwraca listę ze szczegółami dotyczącymi komórek zgodnych z sekwencją.

        return: list<_CellInRow> zawiera informacje komórkach zgodnych z sekwencją
        """
        return self.__list_row_data

    @staticmethod
    def get_list_possible_sequence_names() -> list:
        """
        Zwraca listę nazw mozliwych sekwencji kolumn.

        return: list<str> lista rodzajów sekwencji kolumn.
        """
        return [
            'Z kolumną "Klub" oraz bez "PR"',
            'Bez kolumny "Klub" oraz bez "PR"'
        ]

    def set_sequence_columns(self, name_sequence_columns: str) -> bool:
        """
        Funkcja ustawia w obiekcie nową listę sekwencji.

        return: bool - True jeżeli udało się ustawić wybraną sekwencję, False jeżeli nie udało się znaleźć sekwencji o
                        wybranej nazwie
        """
        match name_sequence_columns:
            case 'Z kolumną "Klub" oraz bez "PR"':
                self.__sequence_columns = [0, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                self.__obj_to_reading_data_from_image.update_indexes_of_columns(0, 3, 12)
            case 'Bez kolumny "Klub" oraz bez "PR"':
                self.__sequence_columns = [0, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                self.__obj_to_reading_data_from_image.update_indexes_of_columns(0, 2, 11)
            case _:
                Informing().error(f"Nie istnieje sekwencja kolumn o nazwie {name_sequence_columns}.")
                return False
        return True

    def get_row_data(self, img_frame: np.ndarray) -> list[_CellInRow]:
        """
        Funkcja przeszukuje przekazany obraz w poszukiwaniu wierszy z komórkami spełniającymi wymagania sekwencji,
        oraz zwraca list<_CellRow>.

        Funkcja przeszukuje przekazany obraz w poszukiwaniu wszystkich dostępnych komórek, które zapisuje
        w self.__list_all_row_data_in_img, natomiast w self.__list_row_data zapisuje te komórki, które spełniają
        założenia self.__sequence_columns

        :params img_frame: kolorowy obraz z kamery
        return: list<_CellInRow> zawiera informacje o komórkach które spełniają warunki
        """
        self.__list_all_row_data_in_img, self.__list_row_data = [], []
        if not isinstance(img_frame, np.ndarray):
            return []

        img_frame_black = self.__to_black_image(img_frame)
        array_coord_y = self.__looking_for_row(img_frame_black)

        for coord_y in array_coord_y:
            y0, y1 = coord_y
            img_row_black = img_frame_black[y0:y1]
            array_coord_x = self.__looking_for_column(img_row_black)

            array_coord_x_after_check_sequence = self.__finding_sequence(array_coord_x)
            if array_coord_x_after_check_sequence:
                self.__list_row_data.append(_CellInRow(coord_y, array_coord_x_after_check_sequence))
            self.__list_all_row_data_in_img.append(_CellInRow(coord_y, array_coord_x))
        return self.__list_row_data

    def __looking_for_row(self, img_frame_black: np.ndarray) -> list:
        """
        Funkcja służy do pośredniczenia między wywołaniem w poszukiwaniu wierszy a self.__create_coord_array.

        :param img_frame_black: czarno-biały obrazy z kamery
        :return: list<list<int, int>> lista dwuelementowych list zawiera górne i dolne współrzędne znalezionych wierszy
        """
        return self.__create_coord_array(
            img=img_frame_black,
            min_space=self.__MIN_HEIGHT,
            threshold=self.__THRESHOLD_HORIZONTAL,
            looking_row=True
        )

    def __looking_for_column(self, img_frame_black: np.ndarray) -> list:
        """
        Funkcja służy do pośredniczenia między wywołaniem w poszukiwaniu komórek w wierszu a self.__create_coord_array.

        :param img_frame_black: (np.ndarray) czarno-biały obrazy z kamery
        :return: list<list<int, int>> lista dwuelementowych list z lewymi i prawymi współrzędnymi komórkami w wierszu
        """
        return self.__create_coord_array(
            img=img_frame_black,
            min_space=self.__MIN_WIDTH,
            threshold=self.__THRESHOLD_VERTICAL,
            looking_row=False
        )

    @staticmethod
    def __to_black_image(img: np.ndarray) -> np.ndarray:
        """
        Funkcja zamienia obraz na czarno-biały.

        Jeżeli obraz jest kolorowy (ma 3 wymiary) jest zamieniany na obraz szary,
        jeżeli nie to odrazu jest zamieniany na czarno-biały

        :param img: kolorowy lub szary obraz obraz
        :return: czarno-biały obraz
        """
        if len(img.shape) == 3:
            img = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2GRAY)
        t_val = threshold_local(image=img, block_size=17, offset=10, method='gaussian')
        return (img > t_val).astype('uint8') * 255

    @staticmethod
    def __create_coord_array(img: np.ndarray, min_space: int, threshold: int, looking_row: bool) -> list:
        """
        Funkcja ma za zadanie zwrócenie list z współrzędnymi
            - y0 y1 przy looking_row==True
            - x0 x1 przy looking_row==False.

        Jeżeli looking_row==False to obraz jest okręcany o 270 stopni,
        aby pierwsza kolumna odpowiadała po przekształceniu pierwszemu wierszowi

        Tablica array_all_wsp przechowuje współrzędne wszystkich wierszy,
        których średnia wartość jest większa niż threshold

        Tablica array_coord, czyli ta która jest zwracana, przechowuje współrzędne zaczynające i kończące sekwencję
        kolejnych współrzędnych z array_all_wsp, ale różnica między początkiem a końcem musi być >= minSpace

        :param img: czarno-biały obraz
        :param threshold: próg średniej, jeżeli średnia wartość przekroczy tą granicę to współrzędna jest zapisywana
                          w tablicy do array_all_wsp
        :param looking_row: zmienna określa czy sprawdzane są wiersze(True) czy kolumny(False)
        :param min_space: ta zmienna określa minimalną odległość między wsp0 a wsp1
        :return: list<list<int, int>> gdzie pod 0 indeksem jest początkowa współrzędna, a pod 1 jest końcowa współrzędna
        """
        img = img.copy()
        if not looking_row:
            img = np.rot90(img, 3)

        array_all_coord = []
        for coord, line in enumerate(img):
            if np.sum(line) > threshold * len(line):
                array_all_coord.append(coord)

        array_coord = []
        len_array = len(array_all_coord)
        coord_0 = 0
        for i, coord_now in enumerate(array_all_coord):
            if i == 0 or array_all_coord[i - 1] < coord_now - 1:
                coord_0 = coord_now
            if i == len_array - 1 or array_all_coord[i + 1] > coord_now + 1:
                if coord_now - coord_0 >= min_space:
                    array_coord.append([coord_0, coord_now + 1])
        return array_coord

    def __finding_sequence(self, array_coord_x: list) -> list | bool:
        """
        Funkcja szukająca sekwencji współrzędnych coord_x, których szerokość spełnia sequenceColumns.

        Najpierw sprawdza czy jest wystarcająca ilość kolumn, aby dało się znaleźć sekwencję.
        Następnie sprawdza każdą możliwą sekwencję do znalezienia pasującej:
            Sprawdza czy sekwencja jest spełniona, a następnie czy zapisane szerokości są rosnące,
            jeżeli tak to zwraca znalezioną sekwencję
        Jeżeli nie udało się znaleźć to zwraca False

        :param array_coord_x: list<list<int, int>> lista dwuelementowych list z początkiem i końcem kolumny
        :return: list<list<int, int>> | False -  lista dwuelementowych list z współrzędnymi spełniającymi wymagania,
                 lub False jeżeli nie znaleziono sekwencji
        """
        len_sequence = len(self.__sequence_columns)
        how_many_column = len(array_coord_x)
        if how_many_column < len_sequence:
            return False

        for firstX in range(how_many_column - len_sequence):
            array_width = np.full(max(self.__sequence_columns) + 1, -1)
            is_matched = True
            for nr_sequence, index_width in enumerate(self.__sequence_columns):
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
            width_is_growing, cell_next_to_the_cell = True, True
            for x in range(len(array_width) - 1):
                if array_width[x] >= array_width[x + 1]:
                    width_is_growing = False
                    break
                if array_coord_x[firstX + x][1] + self.__MAX_SPACE_BETWEEN_COLUMN < array_coord_x[firstX + 1 + x][0]:
                    cell_next_to_the_cell = False
            if is_matched and width_is_growing and cell_next_to_the_cell:
                return array_coord_x[firstX:firstX + len_sequence]
        return False

    def drawing_cells_in_image(self, img: np.ndarray) -> np.ndarray:
        """
        Funkcja służy do wyrysowania komórek które spełniają założenia sekwencji na przekazanym obrazie.

        :param img: obraz
        :return - obraz z wymalowanymi komórkami
        """
        return self.__drawing_cells(img, self.__list_row_data)

    def drawing_all_cells_in_image(self, img: np.ndarray) -> np.ndarray:
        """
        Funkcja służy do wyrysowania wszystkich komórek na przekazanym obrazie.

        :param img: obraz
        :return - obraz z wymalowanymi komórkami
        """
        return self.__drawing_cells(img, self.__list_all_row_data_in_img)

    @staticmethod
    def __drawing_cells(img: np.ndarray, list_row_data: list[_CellInRow]) -> np.ndarray:
        """
        Funkcja maluje komórki na obrazie według danych przekazanych w list_row_data.

        :param img - obraz
        :list_row_data - lista z obeiktami _CellInRow zawierające informacje o wierszach i komókach w tych wierszach
        :return - obraz z wyrysowanymi komórkami
        """
        for row_data in list_row_data:
            y0, y1 = row_data.get_coord_y()
            for x0, x1 in row_data.get_list_coord_x():
                cv2.rectangle(img, (x0, y0), (x1, y1), (0, 0, 255), 3)
        return img

import numpy as np
import cv2
from skimage.filters import threshold_local

class LookingForPlayerTables:
    """
    Biblioteki:
        from skimage.filters import threshold_local
    """
    def __init__(self):
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
        Klasa do przechowywania współrzędnych y0 y1 wiersza
        oraz tablicy obiektów z współrzędnymi x0 x1

        :param coord_y: (array) tablica przechowująca pod 0 indeksem y0, a pod 1 y1
        :param array_coord_x: (array) tablica przechowuje tablice, w których pod 0 indeksem jest x0, a pod 1 x1
        """

        def __init__(self, coord_y, array_coord_x):
            """
            :param coord_y: (array) pod indeksem 0 przechowuje y0, a pod indeksem 1 przechowuje y1
            :param array_coord_x: (array) tablica przechowuje tablice, w których pod 0 indeksem jest x0, a pod 1 x1
            """
            self.__coord_y = coord_y
            self.__array_coord_x = array_coord_x

        def get_coord_y(self):
            """:return: zwraca y0 y1"""
            return self.__coord_y[0], self.__coord_y[1]

        def get_list_coord_x(self):
            return self.__array_coord_x

        def get_coord_x(self, index_coord_x):
            """
            Funkcja zwraca x0, x1 z kolumny o indeksie 'index_coord_x'
            :param index_coord_x: (int) indeks kolumny
            :return: zwraca x0 x1
            """
            return self.__array_coord_x[index_coord_x][0], self.__array_coord_x[index_coord_x][1]

    @staticmethod
    def get_all_option_sequence_columns():
        return [
            [0, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]

    def get_list_all_row_data_in_img(self):
        return self.__list_all_row_data_in_img

    def get_list_row_data(self):
        return self.__list_row_data

    def set_sequence_columns(self, sequence_columns):
        self.__sequence_columns = sequence_columns

    def get_row_data(self, img_frame):
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
        return self.__create_coord_array(img_frame_black, self.__MIN_HEIGHT,
                                         self.__THRESHOLD_HORIZONTAL, looking_row=True)

    def __looking_for_column(self, img_frame_black):
        return self.__create_coord_array(img_frame_black, self.__MIN_WIDTH,
                                         self.__THRESHOLD_VERTICAL, looking_row=False)

    @staticmethod
    def __to_black_image(img):
        """
        Funkcja zamienia obraz na czarno-biały. Jeżeli obraz jest kolorowy (ma 3 wymiary) jest zamieniany na obraz szary,
        jeżeli nie to odrazu jest zamieniany na czarno-biały

        :param img: (np.ndarray) kolorowy lub szary obraz obraz
        :return: (np.ndarray) zwraca czarno-biały obraz
        :raises brakObrazu: (bool) False gdy nie przekazano zmiennej o typie np.ndarray
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
            - y0 y1 przy check_horizontal==True
            - x0 x1 przy check_horizontal==False

        Jeżeli checkHorizontal==False to obraz jest okręcany o 270 stopni,
        aby pierwsza kolumna odpowiadała po przekształceniu pierwszemu wierszowi

        Tablica array_all_wsp przechowuje współrzędne wszystkich wierszy,
        których średnia wartość jest większa niż threshold

        Tablica array_coord, czyli ta która jest zwracana, przechowuje współrzędne zaczynające i kończące sekwencję
        kolejnych współrzędnych z array_all_wsp, ale różnica między początkiem a końcem musi być >= minSpace

        :param img: (np.ndarray) czarno-biały obraz
        :param threshold: (int) próg średniej, jeżeli średnia wartość przekroczy tą granicę
                                to współrzędna jest zapisywana w tablicy do array_all_wsp
        :param check_horizontal: (bool) zmienna określa czy sprawdzane są wiersze(True) czy kolumny(False)
        :param min_space: (int) ta zmienna określa minimalną odległość między wsp0 a wsp1
        :return: zwraca tablicę tablic, gdzie pod 0 indeksem jest początkowa współrzędna, pod indeksem 1 końcowa współrzędna
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
        :param list_sequence_columns: (array) tablica zawiera cyfry całkowite, kolejno od 0.
                                    Mniejsza wartość oznacza węższą kolumnę. Między kolumnami o tej samej wartości
                                    w tablicy sequenceColumns może się różnić o od *0.9 do *1.1
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

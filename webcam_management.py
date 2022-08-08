"""Moduł odpowiedzialny za zarządzanie kamerą (pobieranie listy kamer, wybieranie kamery i dawanie klatki w kamery."""

import numpy as np
import cv2


class WebcamManagement:
    """
    Obiekt do zarządzania kamerami, wybierania kamer i dostarczania obrazu z kamer.

    get_list_index_webcam() -> list[str] - pobranie indeksów dostępnych kamer
    change_index_chosen_webcam(str) -> bool - zmiana wybranej kamery
    get_frame_from_webcam(str) -> False|np.ndarray - jeżeli int podany to zmiana kamery. Podanie klatki obrazu
    remove_chosen_webcam() -> None - usuwa z pamięci obiektu która kamera była używana
    get_index_chosen_webcam() -> str - zwraca index kamery aktualnie używanej
    """
    def __init__(self):
        """
        __chosen_index_webcam - wybrana kamera, jak nie wybrano to -1
        __list_index_webcam - lista dostępnych kamer (generowana w metodzie get_list_index_webcam), wybrana kamera
                              przez użytkownika musi być na tej liście
        __chosen_webcam_videocapture - jeżeli użytkowik wybrał kamerę to tu będzie obiekt cv2.VideoCapture tej kamery
        """
        self.__chosen_index_webcam: str = "-1"
        self.__list_index_webcam: list[str] = []
        self.__chosen_webcam_videocapture: None | cv2.VideoCapture = None

    def get_list_index_webcam(self) -> list[str]:
        """
        Metoda do wykrycia pod jakimi indeksami są dostępne kamery.

        Indeksy są sprawdzane od 0 do 10, pozatym są odrzucane kamery, których obraz jest praktycznie w pełni czarny.
        :return: lista indeksów z dostępnymi kamerami
        """
        index = 0
        list_webcam = []
        while index < 10:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            read_frame = cap.read()
            if read_frame[0]:
                frame = read_frame[1]
                frame = cv2.resize(frame, (200, 200), interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2GRAY)
                frame = cv2.threshold(src=frame, thresh=10, maxval=1, type=cv2.THRESH_BINARY)[1]
                if np.sum(frame) > 100 * 200 * 0.1:
                    list_webcam.append(str(index))
            cap.release()
            index += 1
        self.__list_index_webcam = list_webcam
        if len(list_webcam):
            self.change_index_chosen_webcam(list_webcam[0])
        return list_webcam

    def change_index_chosen_webcam(self, new_index: str) -> bool:
        """
        Metoda do zmiany wybranej kamery.

        Metoda sprawdza czy pod wybranym indeksem jest dostępna kamera (została wykryta) oraz próbuje nawiązać
        połączenie. Jak się coś nie uda to zwraca Fasle, jak wszystko się udało zwraca True.

        :param new_index: <str> numer kamery
        return: <bool> True jeżeli kamera została mieniowa, False jeżeli
        """
        if new_index not in self.__list_index_webcam:
            return False
        print("Wybrana kamera "+new_index)
        self.remove_chosen_webcam()
        self.__chosen_index_webcam = new_index
        obj_videocapture = cv2.VideoCapture(int(new_index), cv2.CAP_DSHOW)
        if obj_videocapture.isOpened():
            self.__chosen_webcam_videocapture = obj_videocapture
            self.__chosen_webcam_videocapture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.__chosen_webcam_videocapture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            return True
        else:
            return False

    def get_frame_from_webcam(self, new_index: str = "-1") -> bool | np.ndarray:
        """
        Metoda do pobrania aktualnego obrazu z kamery. Dodatkowo można przed pobraniem zmienić wybraną kamerę.

        :param new_index: jeżeli różne od -1 to znaczy że użytkownik chce zmienić kamerę
        :return: False jeżeli być błąd, np.ndarray (obraz z kamery) jeżeli wszysko się udało
        """
        if new_index != "-1":
            if not self.change_index_chosen_webcam(new_index):
                return False
        if self.__chosen_webcam_videocapture is None:
            return False
        if not self.__chosen_webcam_videocapture.isOpened():
            return False
        boolean, frame = self.__chosen_webcam_videocapture.read()
        if boolean:
            return cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)
        else:
            return False

    def remove_chosen_webcam(self) -> None:
        """Metoda do rozłączenia się z aktualnie używaną kamerą."""
        if self.__chosen_webcam_videocapture is not None:
            self.__chosen_webcam_videocapture.release()
        self.__chosen_webcam_videocapture = None
        self.__chosen_index_webcam = "-1"

    def get_index_chosen_webcam(self) -> str:
        """
        Zwraca aktualny index używanej kamery, jak nie jest wybrana to -1.

        return: <int> index wybranej kamery, jak nie zoastałą wybrana to zwrócone zostanie -1
        """
        return self.__chosen_index_webcam

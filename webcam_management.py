"""Moduł odpowiedzialny za zarządzanie kamerą (pobieranie listy kamer, wybieranie kamery i dawanie klatki w kamery."""
import numpy as np
import cv2
from typing import Union


class WebcamManagement:
    """
    Obiekt do zarządzania kamerami, wybierania kamer i dostarczania obrazu z kamer.

    get_list_index_webcam() -> list[int] - pobranie indeksów dostępnych kamer
    change_index_chosen_webcam(int) -> bool - zmiana wybranej kamery
    get_frame_from_webcam(int) -> False|np.ndarray - jeżeli int podany to zmiana kamery. Podanie klatki obrazu
    remove_chosen_webcam() -> None - usuwa z pamięci obiektu która kamera była używana
    get_index_chosen_webcam() -> int - zwraca index kamery aktualnie używanej
    """
    def __init__(self):
        """
        __chosen_index_webcam - wybrana kamera, jak nie wybrano to -1
        __list_index_webcam - lista dostępnych kamer (generowana w metodzie get_list_index_webcam), wybrana kamera
                              przez użytkownika musi być na tej liście
        __chosen_webcam_videocapture - jeżeli użytkowik wybrał kamerę to tu będzie obiekt cv2.VideoCapture tej kamery
        """
        self.__chosen_index_webcam: int = -1
        self.__list_index_webcam: list[int] = []
        self.__chosen_webcam_videocapture: Union[None, cv2.VideoCapture] = None

    def get_list_index_webcam(self) -> list[int]:
        """
        Metoda do wykrycia pod jakimi indeksami są dostępne kamery.

        Indeksy są sprawdzane od 0 do momentu, aż jest  dostępna kamera o podanym indeksie, pozatym są odrzucane kameru,
        których obraz jest praktycznie w pełni czarny.
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
                    list_webcam.append(index)
                cap.release()
            index += 1
        self.__list_index_webcam = list_webcam
        return list_webcam

    def change_index_chosen_webcam(self, new_index: int) -> bool:
        """
        Metoda do zmiany wybranej kamery.

        Metoda sprawdza czy pod wybranym indeksem jest dostępna kamera (została wykryta) oraz próbuje nawiązać
        połączenie. Jak się coś nie uda to zwraca Fasle, jk wszystko się udało zwraca True.
        :param new_index: numer kamery
        """
        if new_index not in self.__list_index_webcam:
            return False
        self.remove_chosen_webcam()
        self.__chosen_index_webcam = new_index
        obj_videocapture = cv2.VideoCapture(new_index, cv2.CAP_DSHOW)
        if obj_videocapture.isOpened():
            self.__chosen_webcam_videocapture = obj_videocapture
            return True
        else:
            return False

    def get_frame_from_webcam(self, new_index: int = -1) -> Union[bool, np.ndarray]:
        """
        Metoda do pobrania aktualnego obrazu z kamery. Dodatkowo można przed pobraniem zmienić wybraną kamerę.

        :param new_index: jeżeli różne od -1 to znaczy że użytkownik chce zmienić kamerę
        :return: False jeżeli być błąd, np.ndarray (obraz z kamery) jeżeli wszysko się udało
        """
        if new_index != -1:
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
        self.__chosen_index_webcam = -1

    def get_index_chosen_webcam(self) -> int:
        """Zwraca aktualny index używanej kamery, jak nie jest wybrana to -1."""
        return self.__chosen_index_webcam

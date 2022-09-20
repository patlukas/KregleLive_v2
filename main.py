"""."""
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QGroupBox,
    QVBoxLayout,
    QComboBox,
    QGridLayout,
    QWidget,
    QPushButton,
    QDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QListWidget,
    QMenu
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QTimer, QSize, QEvent
import qimage2ndarray
from skimage.filters import threshold_local
import skimage.filters.thresholding
import gspread
from apiclient import discovery

import gui
import results_to_csv_file
from game_type_management import GameTypeManagement
from webcam_management import WebcamManagement
from management_google_spreadsheets import ManagementGoogleSpreadsheets
from storages_of_players_results import StorageOfAllPlayersScore
from check_table_has_moved import CheckTableHasMoved
import search_players_rows
from get_licenses import GetLicenses
from informing import Informing
import reading_data_from_image
import reading_numbers_from_cell
import creating_main_table
import creating_lane_table
import creating_summary_tables

import json
from _thread import start_new_thread
import time

import cv2


class StartProgram:
    """
    Klasa odpowiedzialna za zarządzanie programem.

    """
    def __init__(self):
        """
        Klasa tworzy potrzebne obiekty do działania programu i uruchamia GUI.

        __obj_to_reading_number_from_cell - obiekt do odczytu wyniku z komórki
        __obj_to_reading_data_from_image - obiekt do odczytu danyych z obrazu
        __obj_to_webcam_management - obiekt da zarządzania kamerą (wybór zmiany, pobranie obrazu)
        __obj_to_get_licenses - obiekt do pobierania danych o licencji
        __obj_to_storages_results - obiekt do przechowywania wyników
        __obj_to_game_type_management - obiekt do zarządzania wyboru rodzaju gry (6 - osobowa, 4 - osobowa liga)
        __obj_to_management_google_spreadsheets - obiekt do zarządzania uruchomieiem i edycją arkusza google
        __obj_to_looking_for_player_tables - obeikt do szukania tabel z wynikami graczy
        __obj_to_create_summary_tables - obiekt do tworzenia tabel z podsumowaniem
        __obj_to_save_data_to_csv_file - obiekt do teorzenia pliku CSV z podsumowaniem
        __list_until_when_the_interruption_in_reading_the_player_score - lista z czasami kiedy mają być sprawdzane
                                                                         rezultaty graczy
        """
        self.__obj_to_reading_number_from_cell = reading_numbers_from_cell.ReadingNumbersFromCell(
            "templates", "unrecognized_sign", "unrecognized_cell", 0.95, 0.9, 0.75
        )
        self.__obj_to_reading_data_from_image = reading_data_from_image.ReadingDataFromImage(
            self.__obj_to_reading_number_from_cell, 0, 3, 12
        )
        self.__obj_to_webcam_management: WebcamManagement = WebcamManagement()
        self.__obj_to_get_licenses: GetLicenses = GetLicenses("settings/main_licenses_settings.json",
                                                              "spreadsheets/config.json")
        self.__obj_to_storages_results: StorageOfAllPlayersScore = StorageOfAllPlayersScore(
            number_of_team=2,
            number_of_player_in_team=6
        )
        self.__obj_to_game_type_management: GameTypeManagement = GameTypeManagement(
            "settings/game_types.json",
            self.__obj_to_storages_results,
            self.__obj_to_get_licenses
        )
        self.__obj_to_management_google_spreadsheets: ManagementGoogleSpreadsheets = ManagementGoogleSpreadsheets(
            "spreadsheets/config.json",
            self.__obj_to_storages_results
        )
        self.__obj_to_looking_for_player_tables = search_players_rows.LookingForPlayerTables(
            self.__obj_to_reading_data_from_image
        )
        self.__obj_to_create_summary_tables = creating_summary_tables.CreatingSummaryTables(
            "tables_for_results/creating_summary_tables_settings.json",
            self.__obj_to_storages_results
        )
        self.__obj_to_save_data_to_csv_file = results_to_csv_file.ResultsToCsvFile(self.__obj_to_storages_results)
        self.__list_until_when_the_interruption_in_reading_the_player_score: list[float] = []
        Informing().clear_log_file()
        self.__run = False
        gui.start_gui(
            self.__obj_to_game_type_management,
            self.__obj_to_webcam_management,
            self.__obj_to_management_google_spreadsheets,
            self.__obj_to_storages_results,
            self.__obj_to_get_licenses,
            self.__obj_to_looking_for_player_tables,
            self.__obj_to_create_summary_tables,
            self.__obj_to_save_data_to_csv_file,
            self.__on_start_program,
            self.__on_stop_program
        )

    def __on_start_program(self):
        """Metoda ustawia zmiennej __run na True i stworzeniem wątku z uruchomionym __run_program."""
        self.__run = True
        start_new_thread(self.__run_program, ())

    def __on_stop_program(self):
        """Metoda odpowiedzialna jest za ustawienie zmiennej __run na False co skutkuje atrzymaniem __run_program."""
        self.__run = False

    def __run_program(self):
        """
        Metoda do zarządzania główną pracą programu.

        Ta metoda jest odpowiedzialna za odczyt obrazu z tabelą, odczytanie z niego wyników, wypisanie wyników w
        tabelach, wpisanie wyników do arkusza google oraz po zakończeniu gry stworzeniem pliku csv i statystyk.
        """
        obj_check_table_has_moved = CheckTableHasMoved()

        path_to_settings_main_table = self.__obj_to_game_type_management.selected_game_type["tables_for_results"]
        path_to_settings_lane_table = self.__obj_to_game_type_management.selected_game_type["tables_for_lane_results"]
        path_to_settings_worksheet = self.__obj_to_game_type_management.selected_game_type["google_spreadsheets"]
        self.__obj_to_management_google_spreadsheets.set_settings_worksheet_by_path_to_json(path_to_settings_worksheet)
        obj_to_create_main_table = creating_main_table.CreatingMainTable(path_to_settings_main_table,
                                                                         self.__obj_to_storages_results)
        obj_to_create_lane_table = creating_lane_table.CreatingLaneTable(path_to_settings_lane_table,
                                                                         self.__obj_to_storages_results)
        affiliation_players = self.__get_affiliation_players()
        ts = 0  # del
        tn = 0  # del
        how_check = 0  # del
        max_time_sleep = 0  # del
        mean_team_sleep = 0  # del

        how_many_players_not_finished_game = self.__set_list_when_will_be_reading_player_results(affiliation_players)

        while self.__run:
            if how_many_players_not_finished_game == 0:
                self.__visualization_results_in_tables_and_in_sheet(obj_to_create_main_table, obj_to_create_lane_table)
                time.sleep(5)
                continue
            frame = self.__obj_to_webcam_management.get_frame_from_webcam()
            if not self.__check_the_scoreboards_position(obj_check_table_has_moved, frame, affiliation_players):
                continue
            t = time.time()  # del
            for i, affiliation_player in enumerate(affiliation_players):
                if not self.__is_it_time_to_check_the_player_results(affiliation_player, i):
                    continue
                how_check += 1  # del
                update_res, tor_nr, nr_throw_in_tor = self.__read_and_save_player_results(frame, affiliation_player, i)
                if not self.__set_time_when_will_be_next_check_player_results(i, update_res, tor_nr, nr_throw_in_tor):
                    how_many_players_not_finished_game -= 1
            self.__obj_to_storages_results.calculate_league_points()
            self.__visualization_results_in_tables_and_in_sheet(obj_to_create_main_table, obj_to_create_lane_table)
            if how_many_players_not_finished_game == 0:
                self.__obj_to_create_summary_tables.create_images_with_summary_results()
                self.__obj_to_save_data_to_csv_file.save_league_results_to_csv_file()
                continue
            tn += 1  # del
            ts += time.time() - t  # del
            time_sleep = self.__calculate_time_to_sleep_and_set_time_to_next_check_player_results()
            mean_team_sleep += time_sleep  # del
            if time_sleep > max_time_sleep:  # del
                max_time_sleep = time_sleep  # del
            # print(time_sleep)  # del
            time.sleep(time_sleep)
            # print("Pobudka")  # del

        print(ts, tn, ts / tn)  # del
        print(max_time_sleep, mean_team_sleep/tn)  # del
        print(how_check)  # del
        cv2.destroyAllWindows()

    def __check_the_scoreboards_position(self, obj_check_table_has_moved: CheckTableHasMoved, frame: np.ndarray | bool,
                                         affiliation_players: list) -> bool:
        """
        Metoda sprawdza położenie tabeli z wynikami oraz sprawdza czy w tabelach jest odpowiednia liczba graczy.

        Jeżeli tablica została przesunięta to zostaje wysłane powiadomienie, jeżeli nie ma obrazu lub odczytana liczba
        wierszy nie odpowiada oczekiwanej liczbie wierszy to program się zatrzymuje na 10 sekund.

        :param obj_check_table_has_moved: obiekt który umożliwia sprawdzenie czy obraz się ruszył
        :param frame: obraz z kamery lub False jeżeli kamera nie udło się odczytać obrazu
        :param affiliation_players: lista przynależności graczy
        :return: <bool> False jeżeli nie udało się wykryć wierszy z wynikami graczy lub True jeżeli wszystko jest OK
        """
        if type(frame) != bool:
            if obj_check_table_has_moved.check_table_has_moved(frame):
                Informing().info("Tabele z wynikami zostały przesunięte.")
                rows = self.__obj_to_looking_for_player_tables.get_row_data(frame)
                if len(rows) == len(affiliation_players):
                    obj_check_table_has_moved.update_cells_after_generate_rows_details(frame, rows, 1)
                    self.__obj_to_reading_data_from_image.update_list_row_data(rows)
                else:
                    time.sleep(10)
                    return False
        else:
            time.sleep(10)
            return False
        return True

    def __is_it_time_to_check_the_player_results(self, affiliation_player: list | None, index_player: int) -> bool:
        """
        Metoda sprawdza czy należy sprawdzać wyniki gracza w tabeli wyników.

        Najpierw sprawdza czy gracz należey do jakiejś drużyny ( w lidze 4 osobowej gracz 3 i 6 na tablicy nie należą)
        Potem jeżeli czas gdy ma być sprawdzany wynik jest ujemny to oznacza że gracz zakończył grę lub jeszcze jej nie
        rozpoczął. A jeżeli czas jeszcze nie nadszedł to gracz musi jeszcze poczekać.

        :param affiliation_player: jeżeli gracz nie należy do żadnej drużyny to None
        :param index_player: numer wiersza w którym są wyniki gracza
        :return: <bool> True jeżeli teraz mają być sprawdzone wyniki gracza, False jeżeli teraz nie mają być sprawdzone
        """
        if affiliation_player is None:
            return False
        if self.__list_until_when_the_interruption_in_reading_the_player_score[index_player] < 0:
            return False
        if self.__list_until_when_the_interruption_in_reading_the_player_score[index_player] > time.time():
            return False
        return True

    def __read_and_save_player_results(self, frame: np.ndarray, affiliation_player: list[int, int], index_player: int
                                       ) -> [int, None | str, None | str]:
        """
        Metoda odczytuje wyniki gracza i zapisuje je w programie.

        :param frame: obraz z tabelą z wynikami
        :param affiliation_player: <list> 1. element to numer zespołu, 2. element to numer gracza w drużynie
        :param index_player: numer wiersza w którym są wyniki gracza
        :return: 1. wartość to 0 jak nie było zmiany, 1 jak wynik się zmienił, 2 jak byl rzut wadliwy,
                    -1 jak gracz skończył, -2 jak nie udało się odczytać
                2. wartośćpusty str jak gracz nie gra aktualnie, str z liczbą określającą na którym torze gra,
                    None jak nie udało się odczytać
                3. wartość str jak udało się odczytać który jest rzut na torze, None jak nie udało się odczytać
        """
        nr_team, nr_player = affiliation_player
        tor_nr, nr_of_throw_tor, player_result = self.__obj_to_reading_data_from_image.read_data_from_row(frame,
                                                                                                          index_player)
        player = self.__obj_to_storages_results.teams[nr_team].players_results[nr_player]
        result_update = player.update_data(tor_nr, nr_of_throw_tor, player_result)
        return [result_update, tor_nr, nr_of_throw_tor]

    def __set_time_when_will_be_next_check_player_results(self, index_player: int, update_result: int,
                                                          tor_nr: None | str, nr_of_throw_in_tor: None | str) -> True:
        """
        Metoda ustawie kiedy ma być następne sprawdzenie wyników gracza.

        :param index_player: w którym wierszu są wyniki gracza
        :param update_result: jaki rezultat został zwrócony po edycji wyników gracza: 0-bez zmian, 1- zmiana wyniku,
                                2 - rzut wadliwy, -1 gracz skończył, -2 błąd w odczycie wyników
        :param tor_nr: numer toru na którym gra gracz, "" jak nie gra, None jeżeli nie udało się odczytać
        :param nr_of_throw_in_tor: numer rzutu na torze, jak nie udało się odczytać to None
        :return: True jeżeli gracz jeszcze gra, False, jeżeli gracz skńczył grę
        """
        if update_result == -1:
            self.__list_until_when_the_interruption_in_reading_the_player_score[index_player] = -4
            return False
        if tor_nr == "":
            self.__list_until_when_the_interruption_in_reading_the_player_score[index_player] = -3
            return True
        waiting_time = 0
        if nr_of_throw_in_tor == "30":
            waiting_time = 0
        elif update_result == 1:
            waiting_time = 17
        elif update_result == 2:
            waiting_time = 8
        waiting_time /= 2
        self.__list_until_when_the_interruption_in_reading_the_player_score[index_player] = time.time() + waiting_time
        return True

    def __visualization_results_in_tables_and_in_sheet(self, obj_to_create_main_table: creating_main_table,
                                                       obj_to_create_lane_table: creating_lane_table) -> None:
        """
        Metoda tworzy tablice z wynikami oraz wypisuje wyniki w arkuszu google.
        :param obj_to_create_lane_table: obiekt do tworzenia głównej tabeli z wynikami
        :param obj_to_create_main_table: obekt do tworzenia tabel z wynikami na poszczególnych torach
        """
        obj_to_create_main_table.make_table()
        obj_to_create_lane_table.make_table()
        self.__obj_to_management_google_spreadsheets.update_data_in_worksheet()
        cv2.waitKey(1)

    def __calculate_time_to_sleep_and_set_time_to_next_check_player_results(self) -> float:
        """
        Metoda oblicza na ile czasu ma być program uśpiony.

        Jeżeli wszyscy gracze którzy grali już skończyli grę to czas oczekiwania graczy, którzy mieli -3 zmianiany jest
        na aktualny czas + 75s

        :return: <float> na ile sekund ma być uśpiony program
        """
        when_next_reading_results = -1
        for time_next_reading_player_result in self.__list_until_when_the_interruption_in_reading_the_player_score:
            if time_next_reading_player_result < 0:
                continue
            if when_next_reading_results == -1 or when_next_reading_results > time_next_reading_player_result:
                when_next_reading_results = time_next_reading_player_result

        if when_next_reading_results == -1:
            when_next_reading_results = time.time() + 75
            for i in range(len(self.__list_until_when_the_interruption_in_reading_the_player_score)):
                if self.__list_until_when_the_interruption_in_reading_the_player_score[i] == -3:
                    self.__list_until_when_the_interruption_in_reading_the_player_score[i] = when_next_reading_results

        time_sleep = when_next_reading_results - time.time()
        if time_sleep < 1:
            time_sleep = 1
        return time_sleep

    def __set_list_when_will_be_reading_player_results(self, affiliation_players: list[list[int, int] | None]) -> int:
        """
        Metoda ustala kiedy mają być sprawdzane wyniki graczy i zwraca ilu graczy gra.

        Jeżeli gracz nie niest w żadnej drużynie to ustawiane jest -1 (nigdy nie będą sprawdzane wyniki) w przeciwnym
        przypadku ustawiany jest aktualny czas.

        :param affiliation_players: <list<int>> jeżeli gracz należy do drużyny, None jak nie należy
        :return: ilu graczy bierze udział w meczu
        """
        self.__list_until_when_the_interruption_in_reading_the_player_score = []
        how_many_players_not_finished_game = 0
        for affiliation_player in affiliation_players:
            waiting_time = time.time()
            if affiliation_player is None:
                waiting_time = -1
            how_many_players_not_finished_game += 1
            self.__list_until_when_the_interruption_in_reading_the_player_score.append(waiting_time)
        return how_many_players_not_finished_game

    def __get_affiliation_players(self) -> list[list[int] | None]:
        """."""
        affiliation_of_players_to_teams = self.__obj_to_game_type_management.selected_game_type[
            "affiliation_of_players_to_teams"
        ]
        index_player_in_team = {}
        affiliation_players = []
        for nr_team in affiliation_of_players_to_teams:
            if nr_team != -1:
                nr_player = index_player_in_team.get(nr_team, -1) + 1
                affiliation_players.append([nr_team, nr_player])
                index_player_in_team[nr_team] = nr_player
            else:
                affiliation_players.append(None)
        return affiliation_players


if __name__ == '__main__':
    StartProgram()

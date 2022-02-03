"""Moduł odpowiedzialny za zapisywanie wyników do arkusza kalkulacyjnego od Google."""

import gspread
import logging
import logging_config
import json
from datetime import datetime
from storages_of_players_results import StorageOfAllPlayersScore

from apiclient import discovery
from google.oauth2 import service_account


class ManagementGoogleSpreadsheets:
    """
    Klasa do zarządzania łączeniem ze skoroszytem, wybieraniem arkusza i zapisywaniem danych.

    list_name_worksheet: list<str> - lista dostępnych w skoroszycie nazw arkuszy
    connecting_to_spreadsheet_by_link(str) -> int - próbuje się połączyć z skoroszytem z podanego linku
    disconnecting_to_spreadsheet() -> None - rozłączenie ze skoroszytem
    connecting_to_worksheet_by_name(str) -> bool - połączenie z arkuszem o podanej nazwie ze skoroszytu
    disconnecting_to_worksheet() -> list[str] - rozłącza się z arkuszem i zwraca listę nazw dostępnych arkuszy
    set_obj_to_storages_of_players_results(StorageOfAllPlayersScore) -> None - aktualizuje obiekt z wynikami graczy
    update_data_in_worksheet() -> int - aktualizuje wartości w arkuszu
    """
    def __init__(self, path_config_spreadsheets: str, path_settings_worksheet: str,
                 obj_with_results: StorageOfAllPlayersScore | None = None):
        """
        __obj_to_storage_results - obikt przechowujący wyniki/nazwy graczy i drużyn lub None jak nie podano obiektu
        __client - obiekt "klient" do łączenia się z arkuszami, ten użytkownik musi mieć prawo edycji dokumentu, może
                    być wartość None jeżeli nie udało się pobrać danych o kliencie z pliku
        __settings_worksheet - ustawienia arkusza z wynikami, czyli gdzie się znajdują komórki z jakimi danymi
        __spreadsheet - obiekt połączonego skoroszytu lub None jeżeli nie jest aktualnie z niczym połączony
        list_name_worksheet - lista dostępnych w skoroszycie nazw arkuszy
        __worksheet - wybrany arkusz ze skoroszytu
        __saved_players_data_in_worksheet - zapisane dane w arkuszu {"players": {<kind>: <val>,}, "teams": {<k>: <v>,}}
        """
        self.__obj_to_storage_results: StorageOfAllPlayersScore | None = obj_with_results
        self.__client: gspread.client.Client | None = self.__get_gspread_client(path_config_spreadsheets)
        self.__settings_worksheet: dict | None = self.__get_settings_worksheet(path_settings_worksheet)
        self.__path_to_config: str = path_config_spreadsheets
        self.__spreadsheet: gspread.spreadsheet.Spreadsheet | None = None
        self.list_name_worksheet: list[str] = []
        self.__worksheet: gspread.worksheet.Worksheet | None = None
        self.__saved_players_data_in_worksheet: dict = {}

    @staticmethod
    def __get_gspread_client(path_config_spreadsheets: str) -> gspread.Client | None:
        """
        Metoda próbuje pobrać ustawienia klienta połączenia i stworzyć jego obiekt, inaczej None

        :param path_config_spreadsheets: ścieżka do json z konfiguracją klienta
        :return: obiekt klienta - jak udało się połączć, None jak połączenie się nie udało
        """
        try:
            return gspread.service_account(filename=path_config_spreadsheets)
        except FileNotFoundError:
            logging.warning(f"Nie znaleziono pliku z konfiguracją klienta {path_config_spreadsheets}")
            return None

    @staticmethod
    def __get_settings_worksheet(path_settings_worksheet: str) -> dict | None:
        """
        Metoda pobiera ustawienia arkusza z pliku json.

        :param path_settings_worksheet: ścieżka do ustawień arkusza (w jakiej komórce mają znajdować się jakie wyniki)
        :return: dict - po pomyślnym załadowaniu danych, None jak nie znaleziono pliku
        """
        try:
            file = open(path_settings_worksheet, encoding='utf8')
            return json.load(file)
        except FileNotFoundError:
            logging.warning(f"Nie można odczytać ustawień arkusza z pliku {path_settings_worksheet}")
            return None

    def connecting_to_spreadsheet_by_link(self, link_to_spreadsheets: str) -> int:
        """
        Metoda próbuje połączyć się ze skoroszytem spod podanego linku.

        :param link_to_spreadsheets: link do arkusza z którym ma być nawiązane połączenie
        :return: Możliwe wyjścia:
                 - 0 - połączenie z arkuszem udało się
                 - 1 - nie można pobrać konfiguracji klienta
                 - 2 - błędny link do arkusza
                 - 3 - klient nie ma uprawnień do edycji skoroszytu
        """
        if self.__client is None:
            return 1
        try:
            self.__spreadsheet = self.__client.open_by_url(link_to_spreadsheets)
            if not self.__check_permission():
                return 3
            self.__get_list_worksheet()
            return 0
        except (gspread.exceptions.NoValidUrlKeyFound, gspread.exceptions.APIError):
            return 2

    def disconnecting_to_spreadsheet(self) -> None:
        """Metoda rozłącza program i skoroszyt."""
        self.__spreadsheet = None
        self.list_name_worksheet = []

    def __check_permission(self) -> bool:
        """
        Metoda sprawdza czy klient może zapisywać i odczytywać w skoroszycie dane.

        :return: True jeżeli klient posiada uprawnienia, False jeżeli klient nie ma wymaganych uprawnień
        """
        try:
            worksheet = self.__spreadsheet.sheet1
            val = worksheet.acell("A1").value
            worksheet.update('A1', val)
            return True
        except gspread.exceptions.APIError:
            return False

    def __get_list_worksheet(self) -> None:
        """
        Metoda zapisująca w obiekcie listę nazw dostępnych arkuszy.
        """
        list_name_worksheet = []
        for spreadsheet in self.__spreadsheet.worksheets():
            list_name_worksheet.append(spreadsheet.title)
        self.list_name_worksheet = list_name_worksheet

    def connecting_to_worksheet_by_name(self, name_worksheet: str) -> bool:
        """
        Metoda do połączenia się z arkuszem o wybranej nazwie ze skoroszytu z którym jest obiekt połączony.

        :param name_worksheet: nazwa arkusza z którym użytkownik chce się połączyć i ktoóry chce edytować
        :return: True jeżeli udało się z arkuszem, False jeżeli wystąpił problem
        """
        if self.__spreadsheet is None:
            return False
        try:
            self.__worksheet = self.__spreadsheet.worksheet(name_worksheet)
            return True
        except gspread.exceptions.WorksheetNotFound:
            return False

    def disconnecting_to_worksheet(self) -> list[str]:
        """
        Moduł rozłącza obiekt z arkuszem, usuwa słownik z zapamiętanymi danymi wpisanymi i zwraca listę nazw arkuszy.

        :return: lista nazw arkuszy które są w skoroszycie
        """
        self.__worksheet = None
        self.__saved_players_data_in_worksheet = {}
        return self.list_name_worksheet

    def set_obj_to_storages_of_players_results(self, obj_with_results: StorageOfAllPlayersScore) -> None:
        """
        Metoda aktualizuje obiekt z przechowujący wyniki graczy i drużyn.

        :param obj_with_results: nowy obiekt z wynikami
        """
        self.__obj_to_storage_results = obj_with_results

    def update_data_in_worksheet(self) -> int:
        """
        Metoda aktualizuje dane w arkuszu.

        Metoda aktualizuje tylko te wartości które różnią się od zapisanych w słowniku __saved_players_data_in_worksheet
        Jeżeli liczba komórek aktualizowanych z wynikami/nazwami graczy i drużyn == 0 to nie odbędzie się aktualizacja.

        :return: Zwracana jest możliwa wartość:
                - -2 - nie podano obiektu przechowującego wyniki graczy
                - -1 - nie ma połączenia z arkuszem
                -  0 - nie zaaktualizowano żadnej komórki
                - >0 - zaaktualizowano podaną ilość komórek
        """
        if self.__obj_to_storage_results is None:
            return -2
        if self.__worksheet is None:
            return -1
        list_to_update = []
        self.__update_players_results(list_to_update)
        self.__update_teams_results(list_to_update)
        if len(list_to_update) == 0:
            return 0
        self.__update_other_data(list_to_update)
        self.__worksheet.batch_update(list_to_update)
        return len(list_to_update)

    def __update_players_results(self, list_to_update: list[dict]) -> None:
        """
        Metoda do wyznaczenia komórek których wartości należy uaktualnić.

        :param list_to_update: lista słowników zawierających współrzędne komórek i ich nowe wartości
        """
        saved_players_data = self.__saved_players_data_in_worksheet.get("players", {})
        for i, player in enumerate(self.__settings_worksheet["players"]):
            index_team, index_player = player["index_team"], player["index_player"]
            saved_player_data = saved_players_data.get(i, {})
            obj_player = self.__obj_to_storage_results.teams[index_team].players_results[index_player]

            for name_result, coords in player["cells"].items():
                result = ""
                if name_result[:11] == "name_player":
                    nr_player = int(name_result[11:]) - 1
                    if len(obj_player.list_name) > nr_player:
                        result = obj_player.list_name[nr_player]
                elif name_result[:6] == "change":
                    nr_change = int(name_result[6:])
                    if len(obj_player.list_when_changes) > nr_change:
                        nr_throw = obj_player.list_when_changes[nr_change]
                        result = f"Zmiana od {nr_throw} rzutu"
                else:
                    result = self.__obj_to_storage_results.get_data_from_player(index_team, index_player, name_result)
                if result != saved_player_data.get(name_result, ""):
                    saved_player_data[name_result] = result
                    list_to_update.append({"range": coords, "values": [[result]]})
            saved_players_data[i] = saved_player_data
        self.__saved_players_data_in_worksheet["players"] = saved_players_data

    def __update_teams_results(self, list_to_update: list[dict]) -> None:
        """
        Metoda do wyznaczenia komórek których wartości należy uaktualnić.

        :param list_to_update: lista słowników zawierających współrzędne komórek i ich nowe wartości
        """
        saved_teams_data = self.__saved_players_data_in_worksheet.get("teams", {})
        for i, team in enumerate(self.__settings_worksheet["teams"]):
            index_team = team["index_team"]
            saved_team_data = saved_teams_data.get(i, {})

            for name_result, coords in team["cells"].items():
                result = self.__obj_to_storage_results.get_data_from_team(index_team, name_result)
                if result != saved_team_data.get(name_result, ""):
                    saved_team_data[name_result] = result
                    list_to_update.append({"range": coords, "values": [[result]]})
            saved_teams_data[i] = saved_team_data
        self.__saved_players_data_in_worksheet["teams"] = saved_teams_data

    def __update_other_data(self, list_to_update: list[dict]) -> None:
        """
        Metoda do wyznaczenia komórek których wartości należy uaktualnić.

        :param list_to_update: lista słowników zawierających współrzędne komórek i ich nowe wartości
        """
        for name_result, coords in self.__settings_worksheet["other"].items():
            result = ""
            if name_result == "time":
                result = datetime.now().strftime("%H:%M:%S")
            list_to_update.append({"range": coords, "values": [[result]]})

    def move_columns_to_right(self) -> bool:
        """
        Metoda przesuwa określoną ilość kolumn w prawo i zostawia wyczyszczone z wyników te kolumny.

        :return:
            False - nie ma połączenia z arkuszem lub skoroszytem lub nie ma dostępu do pliku json
            True - przesunięcie udało się
        """
        if self.__worksheet is None or self.__spreadsheet is None or self.__settings_worksheet is None:
            return False

        try:
            number_of_columns_to_move = self.__settings_worksheet["number_of_columns_to_move_right"]
        except KeyError:
            number_of_columns_to_move = 0

        if number_of_columns_to_move > 0:
            self.__move_columns_to_right(number_of_columns_to_move)
        self.__clear_values_from_cell()
        return True

    def __move_columns_to_right(self, number_of_columns: int) -> None:
        """
        Metoda kopiuje kolumny i ich zawartość i wstawia po prawej stronie od ostatniej kopiowanej kolumny.

        Metoda kopiuje zawartość pierwszych number_of_columns i wstawia je w nowo utworzone kolumny. Jest tworzone
        number_of_columns kolumn po prawej strony od kolumny o numerze number_of_columns.

        :param number_of_columns: ilość kolumn do kopiowania
        """
        scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets"
        ]

        credentials = service_account.Credentials.from_service_account_file(self.__path_to_config, scopes=scopes)
        service = discovery.build('sheets', 'v4', credentials=credentials)

        batch_update = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": self.__worksheet.id,
                            "dimension": "COLUMNS",
                            "startIndex": number_of_columns,
                            "endIndex": 2*number_of_columns
                        },
                        "inheritFromBefore": True
                    }
                },
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": self.__worksheet.id,
                            "startRowIndex": 0,
                            "startColumnIndex": 0,
                            "endColumnIndex": number_of_columns
                        },
                        "destination": {
                            "sheetId": self.__worksheet.id,
                            "startRowIndex": 0,
                            "startColumnIndex": number_of_columns,
                            "endColumnIndex": number_of_columns*2
                        },
                        "pasteType": "PASTE_NORMAL"
                    }
                }
            ]
        }
        request = service.spreadsheets().batchUpdate(spreadsheetId=self.__spreadsheet.id, body=batch_update)
        request.execute()

    def __clear_values_from_cell(self) -> None:
        """Metoda kasuje wartości z komórek, które przechuwują wyniki (komórki z json)."""
        list_to_update = []
        for player in self.__settings_worksheet["players"]:
            for coords in player["cells"].values():
                list_to_update.append({"range": coords, "values": [[""]]})

        for team in self.__settings_worksheet["teams"]:
            for coords in team["cells"].values():
                list_to_update.append({"range": coords, "values": [[""]]})

        for coords in self.__settings_worksheet["other"].values():
            list_to_update.append({"range": coords, "values": [[""]]})
        self.__worksheet.batch_update(list_to_update)

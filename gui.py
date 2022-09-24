"""."""
import sys

import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QGroupBox,
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
    QHBoxLayout,
    QListWidget,
    QMenu
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QTimer, QEvent

import cv2
import qimage2ndarray

from game_type_management import GameTypeManagement
from webcam_management import WebcamManagement
from management_google_spreadsheets import ManagementGoogleSpreadsheets
from storages_of_players_results import StorageOfAllPlayersScore
from creating_summary_tables import CreatingSummaryTables
from results_to_csv_file import ResultsToCsvFile
from get_licenses import GetLicenses
from search_players_rows import LookingForPlayerTables
from informing import Informing


class GUI(QDialog):
    """."""
    def __init__(self, obj_to_game_type_management: GameTypeManagement, obj_to_webcam_management: WebcamManagement,
                 obj_to_management_google_sheet: ManagementGoogleSpreadsheets,
                 obj_to_storages_results: StorageOfAllPlayersScore, obj_to_get_licenses: GetLicenses,
                 obj_to_looking_for_player_tables, obj_to_create_summary_tables, obj_to_save_csv,
                 on_start_program, on_stop_program):
        """."""
        super().__init__()
        self.__init_window()
        self.__obj_to_game_type_management: GameTypeManagement = obj_to_game_type_management
        self.__obj_to_webcam_management: WebcamManagement = obj_to_webcam_management
        self.__obj_to_management_google_spreadsheets: ManagementGoogleSpreadsheets = obj_to_management_google_sheet
        self.__obj_to_storages_results: StorageOfAllPlayersScore = obj_to_storages_results
        self.__obj_to_get_licenses: GetLicenses = obj_to_get_licenses
        self.__obj_with_informing: Informing = Informing()
        self.__obj_to_looking_for_player_tables: LookingForPlayerTables = obj_to_looking_for_player_tables
        self.__obj_to_create_summary_tables: CreatingSummaryTables = obj_to_create_summary_tables
        self.__obj_to_save_csv: ResultsToCsvFile = obj_to_save_csv
        self.__on_start_program = on_start_program
        self.__on_stop_program = on_stop_program
        self.__panel_players: PlayersPanel | None = None
        self.__panel_red_cards: RedCardsResultsPanel | None = None
        self.__layout = QHBoxLayout()
        self.setLayout(self.__layout)
        self.__set_layout()

    def __init_window(self):
        """."""
        self.setWindowTitle("Kręgle Live")
        self.setWindowFlag(Qt.WindowMinimizeButtonHint)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint)
        # self.setFixedWidth(1280)
        self.move(300, 50)
        # self.setStyleSheet("background: #888888;")

    def __set_layout(self):
        """."""
        self.__panel_players = PlayersPanel(
            self.__obj_to_game_type_management,
            self.__obj_to_storages_results,
            self.__obj_to_get_licenses
        )
        self.__panel_red_cards = RedCardsResultsPanel(self.__obj_to_storages_results)

        game_type_selection = GameTypeSelection(self.__obj_to_game_type_management,
                                                self.__obj_to_looking_for_player_tables, self.__after_change_game_type,
                                                self.__on_start_program, self.__on_stop_program)

        column1 = QWidget()
        column1_layout = QGridLayout()
        column1.setLayout(column1_layout)

        column1_layout.addWidget(game_type_selection, 0, 0)
        column1_layout.addWidget(CameraSelection(self.__obj_to_webcam_management), 0, 1)
        column1_layout.addWidget(self.__panel_players, 1, 0, 1, 2)
        column1_layout.addWidget(self.__panel_red_cards, 2, 0, 1, 2)
        column1_layout.addWidget(ConnectToSpreadsheet(self.__obj_to_management_google_spreadsheets), 3, 0, 1, 2)

        column2 = QWidget()
        column2_layout = QGridLayout()
        column2.setLayout(column2_layout)

        column2_layout.addWidget(ShowFrameFromCamera(self.__obj_to_webcam_management, self.__obj_to_looking_for_player_tables), 0, 0)
        column2_layout.addWidget(self.__panel_red_cards, 1, 0)
        column2_layout.addWidget(ErrorPanel(self.__obj_with_informing), 2, 0)
        column2_layout.addWidget(AdditionalOptionPanel(self.__obj_to_create_summary_tables, self.__obj_to_save_csv), 3, 0)

        self.__layout.addWidget(column1)
        self.__layout.addWidget(column2)

    def __after_change_game_type(self):
        self.__panel_players.set_layout()
        self.__panel_red_cards.remove_red_cards()


class GameTypeSelection(QGroupBox):
    """."""
    def __init__(self, obj_to_game_type_management: GameTypeManagement,
                 obj_to_looking_for_player_tables: LookingForPlayerTables,
                 on_after_change_game_type,
                 on_start_program, on_stop_program):
        super().__init__("Wybór rodzaju gry")
        self.__obj_to_game_type_management: GameTypeManagement = obj_to_game_type_management
        self.__obj_to_looking_for_player_tables: LookingForPlayerTables = obj_to_looking_for_player_tables

        self.__on_after_change_game_type = on_after_change_game_type
        self.__on_start_program = on_start_program
        self.__on_stop_program = on_stop_program
        self.__layout = QGridLayout()
        self.__label_types: QLabel | None = None
        self.__label_sequence: QLabel | None = None
        self.__combobox_types: QComboBox | None = None
        self.__combobox_column_sequence: QComboBox | None = None
        self.__button_start: QPushButton | None = None
        self.__button_end: QPushButton | None = None
        self.__label_name_type: QLabel | None = None
        self.__create_widgets()
        self.setLayout(self.__layout)
        self.__layout_to_select_type()

    def __create_widgets(self):
        self.__label_types = QLabel("Rodzaj gry: ")
        self.__label_sequence = QLabel("Jakie kolumny są w pobieranej tabeli z wynikami: ")
        self.__combobox_types = QComboBox()
        self.__combobox_types.addItems(self.__obj_to_game_type_management.list_name_of_game_types)
        self.__combobox_types.currentTextChanged.connect(self.__on_select_game_type)

        self.__button_start = QPushButton("Rozpocznij")
        self.__button_start.clicked.connect(lambda: self.__layout_after_start())

        self.__button_end = QPushButton("Zakończ")
        self.__button_end.clicked.connect(lambda: self.__dialog_to_end())

        self.__label_name_type = QLabel()

        self.__combobox_column_sequence = QComboBox()
        self.__combobox_column_sequence.addItems(
            self.__obj_to_looking_for_player_tables.get_list_possible_sequence_names()
        )
        self.__combobox_column_sequence.currentTextChanged.connect(
            self.__obj_to_looking_for_player_tables.set_sequence_columns
        )
        self.__combobox_types.setToolTip("Wybór rodzaju gry")
        self.__combobox_column_sequence.setToolTip("Wybór jakie kolumny znajdują się w tabeli")

    def __on_select_game_type(self, name_type: str):
        self.__obj_to_game_type_management.choose_game_type(name_type)
        self.__on_after_change_game_type()

    def __layout_to_select_type(self):
        """."""
        self.__button_end.setParent(None)
        self.__label_name_type.setParent(None)
        self.__layout.addWidget(self.__label_types, 0, 0)
        self.__layout.addWidget(self.__combobox_types, 0, 1)
        self.__layout.addWidget(self.__label_sequence, 1, 0)
        self.__layout.addWidget(self.__combobox_column_sequence, 1, 1)
        self.__layout.addWidget(self.__button_start, 2, 0, 1, 2)

    def __layout_after_start(self):
        """."""
        self.__on_start_program()

        self.__label_name_type.setText(self.__obj_to_game_type_management.name_of_the_selected_game_type)

        self.__button_start.setParent(None)
        self.__combobox_types.setParent(None)
        self.__combobox_column_sequence.setParent(None)
        self.__label_sequence.setParent(None)
        self.__label_types.setParent(None)
        self.__layout.addWidget(self.__label_name_type, 0, 0)
        self.__layout.addWidget(self.__button_end, 0, 1)

    def __dialog_to_end(self):
        """."""
        dlg = QMessageBox.question(self, "Zakończ", "Czy na pewno chcesz zakończyć?", QMessageBox.Yes | QMessageBox.No)
        if dlg == QMessageBox.Yes:
            self.__layout_to_select_type()
            self.__on_stop_program()


class CameraSelection(QGroupBox):
    """."""
    def __init__(self, obj_to_webcam_management: WebcamManagement):
        super().__init__("Wybór kamery")
        self.__obj_to_webcam_management: WebcamManagement = obj_to_webcam_management
        self.__layout = QGridLayout()
        self.__combobox: QComboBox | None = None
        self.__button_refresh: QPushButton | None = None
        self.__create_widgets()
        self.setLayout(self.__layout)
        self.__set_layout()

    def __create_widgets(self):
        """."""
        self.__combobox = QComboBox()
        self.__combobox.currentTextChanged.connect(self.__obj_to_webcam_management.change_index_chosen_webcam)
        self.__button_refresh = QPushButton("Odśweż listę")
        self.__button_refresh.clicked.connect(self.__set_layout)

    def __set_layout(self):
        """."""
        self.__combobox.clear()
        self.__combobox.addItems(self.__obj_to_webcam_management.get_list_index_webcam())

        self.__layout.addWidget(self.__combobox, 0, 0)
        self.__layout.addWidget(self.__button_refresh, 1, 0)


class ShowFrameFromCamera(QGroupBox):
    """."""
    def __init__(self, obj_to_webcam_management: WebcamManagement,
                 obj_to_looking_for_player_tables: LookingForPlayerTables):
        super().__init__("Obraz z kamery")
        self.__obj_to_webcam_management: WebcamManagement = obj_to_webcam_management
        self.__obj_to_looking_for_player_tables: LookingForPlayerTables = obj_to_looking_for_player_tables
        self.__label_frame_camera: QLabel | None = None
        self.__combobox_type_frame: QComboBox | None = None
        self.__type_frame: int = 0
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.__set_layout()
        self.__show_frame()
        self.__set_interval()

    def __set_layout(self):
        """."""
        self.__label_frame_camera = QLabel()
        self.__label_frame_camera.resize(621, 350)
        self.__label_frame_camera.setAlignment(Qt.AlignCenter)

        self.__combobox_type_frame = QComboBox()
        self.__combobox_type_frame.addItems([
            "Czysty obraz",
            "Obraz z zaznaczonymi komórkami z wynikami graczy",
            "Obraz z zaznaczonymi wszystkimi znalezionymi komórami"
        ])
        self.__combobox_type_frame.currentIndexChanged.connect(self.__change_type_frame)

        self.__layout.addWidget(self.__combobox_type_frame, 0, 0)
        self.__layout.addWidget(self.__label_frame_camera, 1, 0)

    def __change_type_frame(self, type_frame: int):
        self.__type_frame = type_frame

    def __show_frame(self):
        """."""
        frame = self.__obj_to_webcam_management.get_frame_from_webcam()
        if self.__type_frame == 1:
            frame = self.__obj_to_looking_for_player_tables.drawing_cells_in_image(frame)
        elif self.__type_frame == 2:
            frame = self.__obj_to_looking_for_player_tables.drawing_all_cells_in_image(frame)
        if type(frame) == np.ndarray:
            q_image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
            pixmap = QPixmap(q_image)
            pixmap = pixmap.scaled(601, 350, Qt.KeepAspectRatio)
            self.__label_frame_camera.setPixmap(pixmap)

    def __set_interval(self):
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.__show_frame())
        self.timer.start(1000)


class ConnectToSpreadsheet(QGroupBox):
    """."""
    def __init__(self, obj_to_management_google_spreadsheets: ManagementGoogleSpreadsheets):
        super().__init__("Łączenie z arkuszem kalkulacyjnym Google")
        self.__obj_to_management_google_spreadsheets: ManagementGoogleSpreadsheets = obj_to_management_google_spreadsheets

        self.__label_link_to_spreadsheet: QLabel | None = None
        self.__input_link_to_spreadsheet: QLineEdit | None = None
        self.__button_connect_to_spreadsheet: QPushButton | None = None

        self.__label_title_name_spreadsheet: QLabel | None = None
        self.__label_name_spreadsheet: QLabel | None = None
        self.__button_disconnect_to_spreadsheet: QPushButton | None = None
        self.__label_chose_worksheet: QLabel | None = None
        self.__combobox_worksheet: QComboBox | None = None
        self.__button_connect_to_worksheet: QPushButton | None = None

        self.__label_title_name_worksheet: QLabel | None = None
        self.__label_name_worksheet: QLabel | None = None
        self.__button_disconnect_to_worksheet: QPushButton | None = None

        self.__create_widgets()
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.__layout_to_connect_to_spreadsheet()

    def __create_widgets(self):
        """."""
        self.__label_link_to_spreadsheet = QLabel("Link do skoroszytu:")
        self.__input_link_to_spreadsheet = QLineEdit()
        self.__button_connect_to_spreadsheet = QPushButton("Połącz się ze skoroszytem")
        self.__button_connect_to_spreadsheet.clicked.connect(lambda: self.__on_connect_to_spreadsheet())

        self.__label_title_name_spreadsheet = QLabel("Nazwa skoroszytu: ")
        self.__label_name_spreadsheet = QLabel("")
        self.__button_disconnect_to_spreadsheet = QPushButton("Rozłącz skoroszyt")
        self.__button_disconnect_to_spreadsheet.clicked.connect(self.__layout_to_connect_to_spreadsheet)
        self.__label_chose_worksheet = QLabel("Arkusz do edycji")
        self.__combobox_worksheet = QComboBox()
        self.__button_connect_to_worksheet = QPushButton("Wybierz arkusz")
        self.__button_connect_to_worksheet.clicked.connect(self.__layout_connect_worksheet)

        self.__label_title_name_worksheet = QLabel("Wybrany arkusz:")
        self.__label_name_worksheet = QLabel("")
        self.__button_disconnect_to_worksheet = QPushButton("Rozłącz arkusz")
        self.__button_disconnect_to_worksheet.clicked.connect(self.__layout_to_choose_to_worksheet)

    def __remove_layout(self):
        for i in reversed(range(self.__layout.count())):
            self.__layout.itemAt(i).widget().setParent(None)

    def __layout_to_connect_to_spreadsheet(self):
        """."""
        self.__obj_to_management_google_spreadsheets.disconnecting_to_spreadsheet()

        self.__remove_layout()

        self.__layout.addWidget(self.__label_link_to_spreadsheet, 0, 0)
        self.__layout.addWidget(self.__input_link_to_spreadsheet, 0, 1)
        self.__layout.addWidget(self.__button_connect_to_spreadsheet, 0, 2)

    def __on_connect_to_spreadsheet(self):
        """."""
        link = self.__input_link_to_spreadsheet.text()
        result = self.__obj_to_management_google_spreadsheets.connecting_to_spreadsheet_by_link(link)
        if result:
            dlg = QMessageBox()
            dlg.setWindowTitle("Błąd")
            match result:
                case 1:
                    text = "Nie można znaleźć pliku z konfiguracją klienta."
                case 2:
                    text = "Błędny link do skoroszytu."
                case 3:
                    text = "Klient nie ma uprawnień do edycji skoroszytu."
                case 4:
                    text = "Brak połączenia z internetem."
                case _:
                    text = "Niespodziewany błąd podczas łączenia."
            dlg.setText(text)
            dlg.exec()
        else:
            self.__layout_to_choose_to_worksheet()

    def __layout_to_choose_to_worksheet(self):
        """."""
        self.__obj_to_management_google_spreadsheets.disconnecting_to_worksheet()

        self.__label_name_spreadsheet.setText(self.__obj_to_management_google_spreadsheets.name_spreadsheet)
        self.__combobox_worksheet.clear()
        self.__combobox_worksheet.addItems(self.__obj_to_management_google_spreadsheets.list_name_worksheet)

        self.__remove_layout()

        self.__layout.addWidget(self.__label_title_name_spreadsheet, 0, 0)
        self.__layout.addWidget(self.__label_name_spreadsheet, 0, 1)
        self.__layout.addWidget(self.__button_disconnect_to_spreadsheet, 0, 2)
        self.__layout.addWidget(self.__label_chose_worksheet, 1, 0)
        self.__layout.addWidget(self.__combobox_worksheet, 1, 1)
        self.__layout.addWidget(self.__button_connect_to_worksheet, 1, 2)

    def __layout_connect_worksheet(self):
        """."""
        name_worksheet = self.__combobox_worksheet.currentText()
        self.__obj_to_management_google_spreadsheets.connecting_to_worksheet_by_name(name_worksheet)

        self.__label_name_worksheet.setText(name_worksheet)

        self.__remove_layout()

        self.__layout.addWidget(self.__label_title_name_spreadsheet, 0, 0)
        self.__layout.addWidget(self.__label_name_spreadsheet, 0, 1)
        self.__layout.addWidget(self.__button_disconnect_to_spreadsheet, 0, 2)
        self.__layout.addWidget(self.__label_title_name_worksheet, 1, 0)
        self.__layout.addWidget(self.__label_name_worksheet, 1, 1)
        self.__layout.addWidget(self.__button_disconnect_to_worksheet, 1, 2)


class ErrorPanel(QGroupBox):
    """."""
    def __init__(self, obj_with_informing: Informing):
        super().__init__("Błędy")
        self.__obj_with_informing: Informing = obj_with_informing
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.__table: None | QTableWidget = None
        self.__list_messages: list[dict] = []
        self.__set_layout()
        self.__set_interval()

    def __set_layout(self):
        """."""
        table = QTableWidget()
        table.setColumnCount(3)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setFont(QtGui.QFont("Arial", 6))

        table.setHorizontalHeaderItem(0, QTableWidgetItem("Data"))
        table.setHorizontalHeaderItem(1, QTableWidgetItem("Range"))
        table.setHorizontalHeaderItem(2, QTableWidgetItem("Wiadomość"))

        table.setFocusPolicy(Qt.NoFocus)
        table.setSelectionMode(QAbstractItemView.NoSelection)

        vertical_header = table.verticalHeader()
        vertical_header.setDefaultSectionSize(10)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        self.__layout.addWidget(table, 0, 0)
        self.__table = table
        self.__add_messages()

    def __add_messages(self):
        """."""
        was_added = False
        data = self.__obj_with_informing.get_list_message()
        if len(data) > len(self.__list_messages):
            self.__table.setRowCount(len(data))
        for nr_message in range(len(self.__list_messages), len(data)):
            was_added = True
            self.__list_messages.append(data[nr_message])
            row = data[nr_message]
            self.__table.setItem(nr_message, 0, QTableWidgetItem(row["data"]))
            self.__table.setItem(nr_message, 1, QTableWidgetItem(row["type"]))
            self.__table.setItem(nr_message, 2, QTableWidgetItem(row["text"]))

        if was_added:
            self.__table.scrollToBottom()

    def __set_interval(self):
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.__add_messages())
        self.timer.setInterval(2500)
        self.timer.start()


class PlayersPanel(QGroupBox):
    """."""
    def __init__(
        self,
        obj_to_game_type_management: GameTypeManagement,
        obj_to_storage_results: StorageOfAllPlayersScore,
        obj_to_get_licenses: GetLicenses
    ):
        super().__init__("Ustawianie nazw")
        self.__obj_to_game_type_management: GameTypeManagement = obj_to_game_type_management
        self.__obj_to_storage_results: StorageOfAllPlayersScore = obj_to_storage_results
        self.__obj_to_get_licenses: GetLicenses = obj_to_get_licenses
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.set_layout()

    def set_layout(self):
        """."""
        for i in reversed(range(self.__layout.count())):
            self.__layout.itemAt(i).widget().deleteLater()
        match self.__obj_to_game_type_management.selected_game_type.get("type", ""):
            case "league":
                widget = LeaguePlayerPanel(
                    self.__obj_to_game_type_management,
                    self.__obj_to_storage_results,
                    self.__obj_to_get_licenses
                )
                self.__layout.addWidget(widget, 0, 0)
            case "competitions":
                pass
            case _:
                Informing().warning(f"Błędny typ gry w wybranym rodzaju gry.")


class LeaguePlayerPanel(QWidget):
    """."""
    def __init__(self, obj_to_game_type_management: GameTypeManagement,
                 obj_to_storage_results: StorageOfAllPlayersScore,
                 obj_to_get_licenses: GetLicenses):
        super().__init__()
        self.__obj_to_game_type_management: GameTypeManagement = obj_to_game_type_management
        self.__obj_to_storage_results: StorageOfAllPlayersScore = obj_to_storage_results
        self.__obj_to_get_licenses: GetLicenses = obj_to_get_licenses
        self.__widgets: list = [{}, {}]
        self.__number_of_changes: int = 0
        self.__number_of_players_in_team: int = 0
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.set_layout()

    def set_layout(self):
        """."""
        selected_game_type = self.__obj_to_game_type_management.selected_game_type
        self.__number_of_players_in_team = selected_game_type.get("number_of_player_in_team", 0)
        self.__number_of_changes = selected_game_type.get("number_of_changes", 0)
        self.__widgets = [{}, {}]
        self.__layout.addWidget(self.__league_column("Gospodarze", self.__widgets[0]), 0, 0)
        self.__layout.addWidget(self.__league_column("Goście", self.__widgets[1]), 0, 1)
        button_save = QPushButton("Zapisz nazwy")
        self.__layout.addWidget(button_save, 1, 0, 1, 2)
        button_save.clicked.connect(self.__on_save_names)

    def __on_save_names(self):
        """."""
        for nr_team, widgets in enumerate(self.__widgets):
            team_name = widgets["input_name_team"].text()
            self.__obj_to_storage_results.teams[nr_team].team_results.set_name(team_name)
            list_names = []
            for combobox_player in widgets["list_combobox_player"]:
                list_names.append([[combobox_player.currentText()], [0]])

            for changes in widgets["list_changes"]:
                if not changes["group_box"].isChecked():
                    continue
                player_in = changes["combobox_player_in"].currentText()
                player_out = changes["combobox_player_out"].currentText()
                number_of_throw = changes["input_number_of_throw"].text()
                try:
                    number_of_throw = int(number_of_throw)
                    number_player_out = int(player_out.replace("Gracz ", "")) - 1
                except ValueError:
                    continue
                list_names[number_player_out][0].append(player_in)
                list_names[number_player_out][1].append(number_of_throw)

            for nr_player, names in enumerate(list_names):
                obj_player = self.__obj_to_storage_results.teams[nr_team].players_results[nr_player]
                obj_player.set_list_name(names[0], names[1])
                obj_player.set_team_name(team_name)

    def __league_column(self, name: str, dict_widgets: dict):
        """."""
        widget = QGroupBox(name)

        combobox_team = QComboBox()
        combobox_team.addItems(self.__obj_to_get_licenses.get_list_team())
        combobox_team.setToolTip("Wybór do której drużyny muszą należeć gracze")

        input_name_team = QLineEdit()

        layout = QGridLayout()
        widget.setLayout(layout)
        layout.addWidget(QLabel("Filtr graczy"), 0, 0)
        layout.addWidget(combobox_team, 0, 1)
        layout.addWidget(QLabel("Nazwa drużyny"), 1, 0)
        layout.addWidget(input_name_team, 1, 1)

        list_combobox_player = []
        for i in range(self.__number_of_players_in_team):
            combobox_player = QComboBox()
            combobox_player.setEditable(True)
            list_combobox_player.append(combobox_player)
            layout.addWidget(QLabel(f"Gracz {i+1}"), 2+i, 0)
            layout.addWidget(combobox_player, 2+i, 1)

        dict_widgets["combobox_team"] = combobox_team
        dict_widgets["input_name_team"] = input_name_team
        dict_widgets["list_combobox_player"] = list_combobox_player
        dict_widgets["list_changes"] = []

        nr_row = self.__number_of_players_in_team + 2
        layout.addWidget(self.__league_column__widget_to_changes(dict_widgets["list_changes"]), nr_row, 0, 1, 2)

        combobox_team.currentTextChanged.connect(lambda: self.__set_list_player_in_combobox(dict_widgets))
        self.__set_list_player_in_combobox(dict_widgets)
        return widget

    def __set_list_player_in_combobox(self, dict_widgets: dict):
        """."""
        name_team = dict_widgets["combobox_team"].currentText()
        dict_widgets["input_name_team"].setText(name_team)
        list_players = self.__obj_to_get_licenses.get_list_player_in_team(name_team)
        for combobox_player in dict_widgets["list_combobox_player"]:
            combobox_player.clear()
            combobox_player.addItems(list_players)

        for change in dict_widgets["list_changes"]:
            combobox_player = change["combobox_player_in"]
            combobox_player.clear()
            combobox_player.addItems(list_players)

    def __league_column__widget_to_changes(self, list_widgets: list):
        """."""
        group_changes = QWidget()
        group_changes_layout = QGridLayout()
        group_changes.setLayout(group_changes_layout)

        list_players = [f"Gracz {i}" for i in range(1, self.__number_of_players_in_team + 1)]
        for i in range(self.__number_of_changes):
            group_box = QGroupBox(f"Zmiana {i + 1}")
            group_box.setCheckable(True)
            group_box.setChecked(False)
            group_box_layout = QGridLayout()
            group_box.setLayout(group_box_layout)

            group_changes_layout.addWidget(group_box, 0, i)

            combobox_players_out = QComboBox()
            combobox_players_out.addItems(list_players)

            input_number_of_throw = QLineEdit()
            input_number_of_throw.setToolTip("Numer rzutu od którego gra zmiennik")

            combobox_player_in = QComboBox()
            combobox_player_in.setEditable(True)

            group_box_layout.addWidget(QLabel("Kto schodzi:"), 0, 0)
            group_box_layout.addWidget(combobox_players_out, 0, 1)
            group_box_layout.addWidget(QLabel("Kiedy zmiana:"), 1, 0)
            group_box_layout.addWidget(input_number_of_throw, 1, 1)
            group_box_layout.addWidget(QLabel("Kto wchodzi:"), 2, 0, 1, 2)
            group_box_layout.addWidget(combobox_player_in, 3, 0, 1, 2)
            widgets = {
                "group_box": group_box,
                "combobox_player_out": combobox_players_out,
                "combobox_player_in": combobox_player_in,
                "input_number_of_throw": input_number_of_throw
            }
            list_widgets.append(widgets)
        return group_changes


class RedCardsResultsPanel(QGroupBox):
    """."""
    def __init__(self, obj_to_storage_results: StorageOfAllPlayersScore):
        super().__init__("Czerwone kartki")
        self.setToolTip("Należy dodawać wszystkie czerwone kartki, gdy gracz dostał ją w zbieranych i trafił więcej "
                        "niż 0 kręgli. (Potrzebne przy generowaniu statystyk)")
        self.__obj_to_storage_results: StorageOfAllPlayersScore = obj_to_storage_results
        self.__label_player: QLabel | None = None
        self.__label_throw: QLabel | None = None
        self.__label_result: QLabel | None = None
        self.__combobox_player: QComboBox | None = None
        self.__combobox_throw: QComboBox | None = None
        self.__combobox_result: QComboBox | None = None
        self.__button_add: QPushButton | None = None
        self.__list_red_cards: QListWidget | None = None
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.set_layout()

    def set_list_players(self):
        """."""
        list_players = []
        if self.__obj_to_storage_results.number_of_teams == 2:
            for name_team in ["Gospodarz", "Gość"]:
                for nr_player in range(1, self.__obj_to_storage_results.number_of_players_in_team+1):
                    list_players.append(f"{name_team} | Gracz {nr_player}")
        else:
            for nr_player in range(1, self.__obj_to_storage_results.number_of_players_in_team + 1):
                list_players.append(f"Gracz {nr_player}")
        self.__combobox_player.clear()
        self.__combobox_player.addItems(list_players)

    def __set_list_throws(self):
        """."""
        nr_team, nr_player = self.__get_nrteam_and_nrplayer_name_player(self.__combobox_player.currentText())
        results = self.__obj_to_storage_results.teams[nr_team].players_results[nr_player].get_list_suma()
        nr_throw_with_result_zero = [""]
        for nr_throw, result in enumerate(results):
            if result == 0:
                nr_throw_with_result_zero.append(str(nr_throw+1))
        self.__combobox_throw.clear()
        self.__combobox_throw.addItems(nr_throw_with_result_zero)

    def __get_nrteam_and_nrplayer_name_player(self, player: str) -> tuple[int, int]:
        """."""
        nr_team = 0
        if self.__obj_to_storage_results.number_of_teams == 2:
            team, player = player.split(" | ")
            nr_team = 0 if team == "Gospodarz" else 1
        nr_player = int(player.replace("Gracz ", "")) - 1
        return nr_team, nr_player

    def set_layout(self):
        """."""
        self.__label_player = QLabel("Kto dostał czerwoną kartkę: ")
        self.__label_throw = QLabel("W którym rzucie dostał kartkę: ")
        self.__label_result = QLabel("Ile zbił wtedy kręgli: ")
        self.__button_add = QPushButton("Dodaj")
        self.__list_red_cards = QListWidget()
        self.__combobox_player = QComboBox()
        self.__combobox_throw = QComboBox()
        self.__combobox_result = QComboBox()
        self.__combobox_result.addItems([str(i) for i in range(10)])
        self.__combobox_player.currentTextChanged.connect(self.__set_list_throws)
        self.__button_add.clicked.connect(self.__add_red_card)
        self.__list_red_cards.installEventFilter(self)
        self.__list_red_cards.setToolTip("Aby usunąć element z listy należy kliknąć prawym przyciskiem myszy.")
        self.set_list_players()

        self.__layout.addWidget(self.__label_player, 0, 0)
        self.__layout.addWidget(self.__combobox_player, 0, 1, 1, 2)
        self.__layout.addWidget(self.__label_throw, 1, 0)
        self.__layout.addWidget(self.__combobox_throw, 1, 1)
        self.__layout.addWidget(self.__label_result, 2, 0)
        self.__layout.addWidget(self.__combobox_result, 2, 1)
        self.__layout.addWidget(self.__button_add, 1, 2, 2, 1)
        self.__layout.addWidget(self.__list_red_cards, 0, 3, 3, 1)

    def __add_red_card(self):
        """."""
        player = self.__combobox_player.currentText()
        throw = self.__combobox_throw.currentText()
        result = self.__combobox_result.currentText()
        if throw == "":
            QMessageBox.about(self, "Uwaga", "Aby dodać czerwoną kartkę należy wybrać w którym rzucie ona była.")
            return
        for i in range(self.__list_red_cards.count()):
            item_row = self.__list_red_cards.item(i)
            if item_row.text().split(" rzucie")[0] == f"{player} otrzymał czerwoną kartkę w {throw}":
                QMessageBox.about(self, "Uwaga", "Gracz dostał już w tym rzucie czerwoną kartkę.")
                return

        self.__list_red_cards.addItem(f"{player} otrzymał czerwoną kartkę w {throw} rzucie, gdy zbił {result} kręgli")
        self.__save_red_card_in_obj_with_results()

    def eventFilter(self, source, event) -> bool:
        """."""
        if event.type() == QEvent.ContextMenu and source is self.__list_red_cards:
            if source.itemAt(event.pos()) is not None:
                menu = QMenu()
                menu.addAction("Usuń")
                if menu.exec_(event.globalPos()):
                    item = source.itemAt(event.pos())
                    list_items = []
                    for i in range(self.__list_red_cards.count()):
                        item_row = self.__list_red_cards.item(i)
                        if item_row.text() != item.text():
                            list_items.append(item_row.text())
                    self.__list_red_cards.clear()
                    self.__list_red_cards.addItems(list_items)
                    self.__save_red_card_in_obj_with_results()
                return True
        return super().eventFilter(source, event)

    def __save_red_card_in_obj_with_results(self):
        """."""
        list_items = []
        for i in range(self.__list_red_cards.count()):
            item_row = self.__list_red_cards.item(i)
            list_items.append(item_row.text())
        for nr_team in range(self.__obj_to_storage_results.number_of_teams):
            for nr_player in range(self.__obj_to_storage_results.number_of_players_in_team):
                self.__obj_to_storage_results.teams[nr_team].players_results[nr_player].list_red_cards = []
        for item in list_items:
            player = item.split(" otrzymał czerwoną kartkę w ")[0]
            throw = int(item.split(" otrzymał czerwoną kartkę w ")[1].split(" rzucie, gdy zbił ")[0])
            result = int(item.split(" rzucie, gdy zbił ")[1].split(" kręgli")[0])
            nr_team, nr_player = self.__get_nrteam_and_nrplayer_name_player(player)
            self.__obj_to_storage_results.teams[nr_team].players_results[nr_player].list_red_cards.append((throw, result))

    def remove_red_cards(self):
        """."""
        for nr_team in range(self.__obj_to_storage_results.number_of_teams):
            for nr_player in range(self.__obj_to_storage_results.number_of_players_in_team):
                self.__obj_to_storage_results.teams[nr_team].players_results[nr_player].list_red_cards = []
        self.__list_red_cards.clear()


class AdditionalOptionPanel(QGroupBox):
    """."""
    def __init__(self, obj_to_create_stat: CreatingSummaryTables, obj_to_save_csv: ResultsToCsvFile):
        super().__init__("Dodatkowe opcje")
        self.__obj_to_create_stat: CreatingSummaryTables = obj_to_create_stat
        self.__obj_to_save_csv: ResultsToCsvFile = obj_to_save_csv
        self.__create_stat: QPushButton | None = None
        self.__save_csv: QPushButton | None = None
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.set_layout()

    def set_layout(self):
        """."""
        self.__create_stat = QPushButton("Stwórz statystyki")
        self.__save_csv = QPushButton("Zapisz wyniki w pliku CSV")
        self.__create_stat.clicked.connect(self.__obj_to_create_stat.create_images_with_summary_results)
        self.__save_csv.clicked.connect(self.__obj_to_save_csv.save_league_results_to_csv_file)
        self.__layout.addWidget(self.__create_stat, 0, 0)
        self.__layout.addWidget(self.__save_csv, 0, 1)


def start_gui(
        obj_to_game_type_management: GameTypeManagement,
        obj_to_webcam_management: WebcamManagement,
        obj_to_management_google_spreadsheets: ManagementGoogleSpreadsheets,
        obj_to_storage_results: StorageOfAllPlayersScore,
        obj_to_get_licenses: GetLicenses,
        obj_to_looking_for_player_tables,
        obj_to_create_summary_tables,
        obj_to_save_csv,
        on_start_program,
        on_stop_program
):
    """."""
    app = QApplication(sys.argv)
    ex = GUI(obj_to_game_type_management, obj_to_webcam_management, obj_to_management_google_spreadsheets,
             obj_to_storage_results, obj_to_get_licenses, obj_to_looking_for_player_tables,
             obj_to_create_summary_tables, obj_to_save_csv,
             on_start_program, on_stop_program)
    ex.show()
    sys.exit(app.exec_())

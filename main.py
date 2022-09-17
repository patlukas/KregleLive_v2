"""."""
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
    """."""
    def __init__(self):
        """."""
        self.__obj_to_reading_number_from_cell = reading_numbers_from_cell.ReadingNumbersFromCell(
            "templates", "unrecognized_sign", "unrecognized_cell", 0.95, 0.9, 0.75
        )
        self.__obj_to_reading_data_from_image = reading_data_from_image.ReadingDataFromImage(
            self.__obj_to_reading_number_from_cell, 0, 3, 12
        )
        self.__obj_to_webcam_management: WebcamManagement = WebcamManagement()
        self.__obj_to_get_licenses: GetLicenses = GetLicenses("settings/main_licenses_settings.json", "spreadsheets/config.json")
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
        self.__obj_to_save_data_to_csv_file = results_to_csv_file.ResultsToCsvFile(
            self.__obj_to_storages_results, "results"
        )
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
        """."""
        self.__run = True
        start_new_thread(self.__run_program, ())

    def __on_stop_program(self):
        """."""
        self.__run = False

    def __run_program(self):
        """."""
        obj_check_table_has_moved = CheckTableHasMoved()

        path_to_settings_main_table = self.__obj_to_game_type_management.selected_game_type["tables_for_results"]
        path_to_settings_lane_table = self.__obj_to_game_type_management.selected_game_type["tables_for_lane_results"]
        path_to_settings_worksheet = self.__obj_to_game_type_management.selected_game_type["google_spreadsheets"]
        self.__obj_to_management_google_spreadsheets.set_settings_worksheet_by_path_to_json(path_to_settings_worksheet)
        obj_to_create_main_table = creating_main_table.CreatingMainTable(path_to_settings_main_table, self.__obj_to_storages_results)
        obj_to_create_lane_table = creating_lane_table.CreatingLaneTable(path_to_settings_lane_table, self.__obj_to_storages_results)
        affiliation_players = self.__get_affiliation_players()

        while self.__run:
            frame = self.__obj_to_webcam_management.get_frame_from_webcam()
            if type(frame) != bool:
                if obj_check_table_has_moved.check_table_has_moved(frame) :
                    print("RUCH")
                    rows = self.__obj_to_looking_for_player_tables.get_row_data(frame)
                    cv2.imshow("L", frame)
                    cv2.waitKey(1)
                    if len(rows) == len(affiliation_players):
                        obj_check_table_has_moved.update_cells_after_generate_rows_details(frame, rows, 1)
                        self.__obj_to_reading_data_from_image.update_list_row_data(rows)
                    else:
                        time.sleep(5)
                        continue
            else:
                time.sleep(5)
                continue

            for i, affiliation_player in enumerate(affiliation_players):
                if affiliation_player is None:
                    continue
                nr_team, nr_player = affiliation_player
                tor_nr, nr_of_throw_in_tor, player_result = self.__obj_to_reading_data_from_image.read_data_from_row(frame, i)
                player = self.__obj_to_storages_results.teams[nr_team].players_results[nr_player]
                player.update_data(tor_nr, nr_of_throw_in_tor, player_result)
            self.__obj_to_storages_results.calculate_league_points()
            obj_to_create_main_table.make_table()
            obj_to_create_lane_table.make_table()
            self.__obj_to_management_google_spreadsheets.update_data_in_worksheet()
            # self.__obj_to_create_summary_tables.create_images_with_summary_results()
            cv2.waitKey(1)
            time.sleep(1)
        cv2.destroyAllWindows()

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
    print("JJJ")

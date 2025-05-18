import flet as ft
from interface import GameUI
from network import NetworkClient

def main(page: ft.Page):
    page.title = "Мафия"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    network = NetworkClient(page)
    game_ui = GameUI(page, network)
    network.set_game_ui(game_ui)


if __name__ == "__main__":
    ft.app(target=main)
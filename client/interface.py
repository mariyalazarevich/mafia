
import asyncio
import json
import flet as ft
from flet.core.types import MainAxisAlignment
from network import NetworkClient

w_style = ft.TextStyle(font_family="Ebbe", color=ft.colors.WHITE, size=26)
r_style = ft.TextStyle(font_family="Ebbe", color=ft.colors.RED, size=26)
l_r_style = ft.TextStyle(font_family="Ebbe", color=ft.colors.RED, size=20)
l_w_style = ft.TextStyle(font_family="Ebbe", color=ft.colors.WHITE, size=20)
with open('client/role.json', 'r', encoding='utf-8') as file:
    jsonroles = json.load(file)

class GameUI:
    def __init__(self, page: ft.Page, network):
        self.page = page
        self.network = network
        self._init_ui()
        self.show_connect_view()
        self.list_players = []
        self.role=""
        self.name=""

    def _init_ui(self):
        self.page.bgcolor = ft.colors.TRANSPARENT
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        self.player_name = ft.TextField(label="Введите имя", text_style=w_style,focused_border_color=ft.colors.RED, cursor_color=ft.colors.RED, label_style=l_r_style)
        self.connect_btn = ft.OutlinedButton(content=ft.Text("Присоединиться", font_family="Ebbe", size=26, color=ft.colors.WHITE), on_click=self.connect,
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
                )
        )
        self.connect_btn.on_hover = lambda e: self.handle_hover(self.connect_btn, e)
        self.role_display = ft.Text()
        self.players_list = ft.ListView(expand=True)
        self.main_column = ft.Column()

    @staticmethod
    def handle_hover(button, e):
        if e.data == "true":
            button.style.side = ft.BorderSide(2, ft.colors.RED)
            button.content.color = ft.colors.RED
        else:
            button.style.side = ft.BorderSide(2, ft.colors.WHITE)
            button.content.color = ft.colors.WHITE
        button.update()

    def show_connect_view(self):
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        self.page.add(
            ft.Column(
                controls=[
                    self.player_name,
                    ft.Row(
                        controls=[self.connect_btn],
                        alignment=MainAxisAlignment.CENTER
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        )

    async def connect(self, e):
        self.name = self.player_name.value
        if await self.network.connect(self.name):
            self.show_waiting_view("Игра начинается...")

    def show_waiting_view(self, text):
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        self.page.controls.append(
            ft.Column(
                controls=[
                    ft.Text(text, style=w_style),
                    ft.ProgressBar(color=ft.colors.RED)
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        )
        self.page.update()

    def show_role_view(self, role: str, players: list, show_duration):
        self.clear_page()
        self.role=role
        players_list = ft.ListView(
            controls=[
                ft.Text(
                    p,
                    style=l_w_style,
                    text_align=ft.TextAlign.CENTER  # Центрирование текста
                ) for p in self.list_players
            ],
            height=200,
        )
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        self.page.controls.append(
            ft.Column(
                controls=[
                    ft.Text(f"Ваша роль: {role}", style=r_style),
                    ft.Divider(),
                    ft.Text("Состав игроков:", style=l_w_style),
                    ft.Container(
                        content=players_list,
                        alignment=ft.alignment.center
                    ),
                    ft.ProgressBar(width=300, color=ft.colors.RED),
                    ft.Text(f"Игра начнется через {show_duration} секунд", style=w_style)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def show_night_phase(self, role: str, players: list):
        self.clear_page()
        title=ft.Text(f"{self.name} : {role}", style=r_style)
        status = ft.Text("Ночная фаза - сделайте свой выбор", style=r_style)
        self.page.controls.append(title)
        self.page.controls.append(status)

        if role == "mafia":
            self._create_mafia_interface(players)
        elif role == "doctor":
            self._create_doctor_interface(players)
        else:
            self.page.controls.append(
                ft.Text("Вы спите... Дождитесь утра", style=w_style)
            )
        self.page.update()

    def not_alive_night_phase(self, role):
        self.clear_page()
        title = ft.Text(f"{self.name} : {role} – Вы мертвы", style=r_style)
        status = ft.Text("Ночная фаза. Дождитесь утра", style=r_style)
        self.page.controls.append(title)
        self.page.controls.append(status)
        self.page.update()

    def _create_mafia_interface(self, players):
        self.target_dropdown = ft.Dropdown(
            options=[ft.DropdownOption(key=p, content=ft.Text(p, style=l_w_style)) for p in players],
            text_style=w_style,
            bgcolor=ft.colors.BLACK,
            label="Выберите жертву",
            border_color=ft.colors.RED,
            label_style=w_style,
            width=500,
        )
        confirm_btn = ft.OutlinedButton(
            content=ft.Text("Выбрать жертву", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            )
        )
        confirm_btn.on_click= lambda e: self._send_mafia_choice(e,confirm_btn)
        confirm_btn.on_hover = lambda e: self.handle_hover(confirm_btn, e)
        self.page.controls.extend([self.target_dropdown, confirm_btn])

    def _create_doctor_interface(self, players):
        self.protect_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(key=p, content=ft.Text(p, style=l_w_style)) for p in players],
            text_style=w_style,
            bgcolor=ft.colors.BLACK,
            label="Выберите игрока для защиты",
            border_color=ft.colors.RED,
            label_style=w_style,
            width=500,
        )
        confirm_btn = ft.OutlinedButton(
            content=ft.Text("Защитить игрока", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            )
        )
        confirm_btn.on_click = lambda e: self._send_doctor_choice(e, confirm_btn)
        confirm_btn.on_hover = lambda e: self.handle_hover(confirm_btn, e)
        self.page.controls.extend([self.protect_dropdown, confirm_btn])

    def _send_mafia_choice(self, e, button):
        if self.target_dropdown.value:
            self.page.run_task(self._async_send_mafia_choice, button)

    async def _async_send_mafia_choice(self, button):
        await self.network.send({
            "type": "night_action",
            "target": self.target_dropdown.value,
            "role": "mafia"
        })
        self.page.controls.append(
            ft.Text(f"Цель {self.target_dropdown.value} выбрана...", style=w_style)
        )
        print(f"Цель {self.target_dropdown.value} выбрана...")
        button.visible = False
        button.disabled = True
        self.page.update()

    def _send_doctor_choice(self, e, button):
        if self.protect_dropdown.value:
            self.page.run_task(self._async_send_doctor_choice, button)

    async def _async_send_doctor_choice(self, button):
        await self.network.send({
            "type": "night_action",
            "target": self.protect_dropdown.value,
            "role": "doctor"
        })
        self.page.controls.append(
            ft.Text(f"Защита для {self.protect_dropdown.value} отправлена...", style=w_style)
        )
        print(f"Защита для {self.protect_dropdown.value} отправлена...")
        button.visible = False
        button.disabled = True
        self.page.update()

    @staticmethod
    def get_day_text(data):
        killed=data.get("killed")
        protected=data.get("protected")
        role=data.get("role")
        if killed==protected:
            return f"Мафия пыталась убить {killed}. Но {protected} получил защиту от доктора."
        else:
            return f"Убит: {killed} ({role}). Получил защиту: {protected}"

    def show_day_phase(self, players: list, night_data):
        self.clear_page()
        title = ft.Text(f"{self.name} : {self.role}", style=r_style)
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        self.vote_dropdown=ft.Dropdown(
            options=[ft.dropdown.Option(key=p, content=ft.Text(p, style=l_w_style)) for p in players],
            border_color=ft.colors.RED,
            bgcolor=ft.colors.BLACK,
            text_style=w_style,
            label="Выберите игрока для голосования",
            label_style=w_style,
            width=500,
                    )
        button=ft.OutlinedButton(
            content=ft.Text("Проголосовать", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
        ))
        button.on_click = lambda e: self.send_vote(e, button)
        button.on_hover=lambda e: self.handle_hover(button, e)
        text=self.get_day_text(night_data)
        self.page.controls.append(title)
        self.page.controls.append(ft.Text("День. Обсуждение", style=w_style))
        self.page.controls.append(ft.Text(text, style=r_style))
        self.page.controls.append(ft.ListView(
                        controls=[ft.Text(p) for p in players],
                        height=200
                    ))
        self.page.controls.append(self.vote_dropdown)
        self.page.controls.append(button)
        self.page.update()

    def not_alive_day_phase(self, players, night_data):
        self.clear_page()
        title = ft.Text(f"{self.name} : {self.role} – Вы мертвы", style=r_style)
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        text = self.get_day_text(night_data)
        self.page.controls.append(title)
        self.page.controls.append(ft.Text("День. Обсуждение", style=w_style))
        self.page.controls.append(ft.Text(text, style=r_style))
        self.page.controls.append(ft.ListView(
            controls=[ft.Text(p) for p in players],
            height=200
        ))
        self.page.update()

    def show_day_result(self, data):
        self.clear_page()
        title1 = ft.Text(f"{self.name} : {self.role}", style=r_style)
        title = ft.Text(data["message"], style=r_style)
        text=ft.Text("Ожидание ночной фазы...", style=w_style)
        self.page.controls.append(ft.Text("День. Обсуждение", style=w_style))
        self.page.controls.append(title1)
        self.page.controls.append(title)
        self.page.controls.append(text)
        self.page.controls.append(ft.ProgressBar(color=ft.colors.RED))
        self.page.update()

    def send_vote(self, e, button):
        if self.vote_dropdown.value:
            self.page.run_task(self._async_send_vote, button)

    async def _async_send_vote(self, button):
        await self.network.send({
            "type": "vote",
            "target": self.vote_dropdown.value,
            "player": self.name
        })
        self.page.controls.append(
            ft.Text(f"Голос отправлен...", style=w_style)
        )
        print(f"Голос {self.vote_dropdown.value} отправлен")
        button.visible = False
        button.disabled = True
        self.page.update()

    def show_countdown(self, seconds: int, players: list):
        self.list_players=players
        players_list = ft.ListView(
            controls=[
                ft.Text(
                    p,
                    style=l_w_style,
                    text_align=ft.TextAlign.CENTER
                ) for p in self.list_players
            ]
        )
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        self.page.add(
            ft.Column(
                [
                    ft.Row(
                        [ft.Text(f"Старт через: {seconds} сек", style=r_style)],
                        alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(
                        content=players_list,
                        alignment=ft.alignment.center
                    ),
                    ft.Row(
                        [ft.ProgressBar(color=ft.colors.RED)],
                        alignment=ft.MainAxisAlignment.CENTER)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def clear_page(self):
        self.page.controls.clear()
        self.page.update()

    def update_players_list(self, players: list):
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        players_list = ft.ListView(
            controls=[
                ft.Text(
                    p,
                    style=r_style,
                    text_align=ft.TextAlign.CENTER
                ) for p in players
            ]
        )
        progress = ft.ProgressBar(
            color=ft.colors.RED,
        )
        self.page.controls.append(
            ft.Column(
                controls=[
                    ft.Row(
                        [ft.Text("Ожидание начала игры...", style=w_style)],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(progress, padding=10),
                    ft.Row(
                        [ft.Text(f"{len(players)}/5 игроков", style=r_style)],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(
                        content=players_list,
                        alignment=ft.alignment.center
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def show_game_over(self, winner: str, roles: dict):
        self.clear_page()
        role_list = ft.ListView(expand=True)
        for name, role in roles.items():
            role_list.controls.append(
                ft.Text(f"{name}: {role}", style=w_style)
            )
        button = ft.OutlinedButton(
            content=ft.Text("Вернуться в лобби", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            on_click=lambda e: self.show_connect_view(),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            )
        )
        button.on_hover=lambda e: self.handle_hover(button, e)
        self.page.add(
            ft.Column(
                [
                    ft.Text(f"Победили: {winner.capitalize()}!", style=r_style),
                    ft.Text("Роли игроков:", style=w_style),
                    ft.Container(role_list, alignment=ft.alignment.center),
                    button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()
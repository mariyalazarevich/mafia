import asyncio
import json
import flet as ft
from flet.core.types import MainAxisAlignment, TextAlign
from network import NetworkClient

w_style = ft.TextStyle(font_family="Ebbe", color=ft.colors.WHITE, size=26)
r_style = ft.TextStyle(font_family="Ebbe", color=ft.colors.RED, size=26)
l_r_style = ft.TextStyle(font_family="Ebbe", color=ft.colors.RED, size=20)
l_w_style = ft.TextStyle(font_family="Ebbe", color=ft.colors.WHITE, size=20)
with open('/Users/marialazarevic/PycharmProjects/mafia/client/role.json', 'r', encoding='utf-8') as file:
    jsonroles = json.load(file)

class GameUI:
    def __init__(self, page: ft.Page, network):
        self.page = page
        self.network = network
        self._init_ui()
        self.show_menu()
        self.list_players = []
        self.role=""
        self.name=""

    def _init_ui(self):
        self.current_view = None
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
        self.chat_messages = ft.ListView(expand=True)
        self.chat_history = []
        self.day_phase_controls = []
        self.chat_input = ft.TextField(
            label="Сообщение",
            multiline=True,
            max_lines=3,
            text_style=l_w_style,
            border_color=ft.colors.RED,
            cursor_color=ft.colors.RED,
            focused_border_color=ft.colors.RED,
            label_style=l_r_style
        )
        self.chat_btn = ft.IconButton(
            icon=ft.icons.SEND,
            icon_color=ft.colors.RED,
            on_click=self.send_chat_message
        )

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
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            icon_color=ft.colors.WHITE,
            on_click=lambda _: self.show_menu()
        )
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(
                src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                fit=ft.ImageFit.COVER
            )
        )
        form_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.player_name,
                    self.connect_btn
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            expand=True
        )
        back_container = ft.Container(
            content=back_button,
            alignment=ft.alignment.top_left,
            padding=10,
            height=100
        )
        self.page.add(
            ft.Stack(
                controls=[
                    form_container,
                    back_container
                ],
                expand=True
            )
        )
        self.page.update()

    async def connect(self, e):
        self.name = self.player_name.value
        try:
            connected = await asyncio.wait_for(
                self.network.connect(self.name),
                timeout=3
            )
            if connected:
                await asyncio.sleep(0.5)
                if self.network.exception:
                    self.player_name.value = ""
                    self.player_name.label = "Это имя уже занято"
                    self.page.update()
                    self.network.exception = False
                else:
                    self.update_players_list(self.network.players)
            else:
                self.show_connection_error()
        except (asyncio.TimeoutError, ConnectionRefusedError):
            self.show_connection_error()
        except Exception as e:
            print(f"Unexpected error: {e}")
            self.show_connection_error()

    def show_role_view(self, role: str, show_duration):
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
                    ft.Text(f"Ваша роль: {jsonroles[role]}", style=r_style),
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
        title=ft.Text(f"{self.name} : {jsonroles[role]}", style=r_style)
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
        title = ft.Text(f"{self.name} : {jsonroles[role]} – Вы мертвы", style=r_style)
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
            return f"Убит: {killed} ({jsonroles[role]}). Получил защиту: {protected}"

    def show_day_phase(self, players: list, night_data):
        self.current_view = "day"
        self.clear_page()
        title = ft.Text(f"{self.name} : {jsonroles[self.role]}", style=r_style)
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
        chat_button = ft.OutlinedButton(
            content=ft.Text("Перейти в чат", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            ))
        chat_button.on_click = lambda e: self.show_chat(e)
        chat_button.on_hover = lambda e: self.handle_hover(chat_button, e)
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
        self.page.controls.append(chat_button)
        self.day_phase_controls = [
            title,
            ft.Text("День. Обсуждение", style=w_style),
            ft.Text(text, style=r_style),
            ft.ListView(controls=[ft.Text(p) for p in players], height=200),
            self.vote_dropdown,
            button,
            chat_button
        ]
        self.page.update()

    def add_chat_message(self, sender: str, message: str):
        self.chat_history.append((sender, message))
        if self.current_view == "chat":
            self.chat_messages.controls = [
                ft.Text(f"{s}: {m}", style=l_w_style)
                for s, m in self.chat_history
            ]
            try:
                self.chat_messages.scroll_to(offset=-1, duration=100)
                self.page.update()
            except Exception as e:
                print(f"Ошибка обновления чата: {e}")

    async def send_chat_message(self, e):
        if self.chat_input.value.strip():
            await self.network.send({
                "type": "chat",
                "message": self.chat_input.value
            })
            self.chat_input.value = ""
            self.page.update()

    def not_alive_day_phase(self, players, night_data):
        self.clear_page()
        self.chat_messages.controls.clear()
        title = ft.Text(f"{self.name} : {jsonroles[self.role]} – Вы мертвы", style=r_style)
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
        self.chat_messages.controls.clear()
        title1 = ft.Text(f"{self.name} : {jsonroles[self.role]}", style=r_style)
        title = ft.Text(data["message"], style=r_style)
        text=ft.Text("Ожидание ночной фазы...", style=w_style)
        self.page.controls.append(ft.Text("День. Обсуждение", style=w_style))
        self.page.controls.append(title1)
        self.page.controls.append(title)
        self.page.controls.append(text)
        self.page.controls.append(ft.ProgressBar(color=ft.colors.RED, width=300))
        self.page.update()

    def show_chat(self, e):
        self.clear_page()
        self.current_view = "chat"
        self.chat_messages.controls = [
            ft.Text(f"{s}: {m}", style=l_w_style)
            for s, m in self.chat_history
        ]
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            icon_color=ft.colors.RED,
            on_click=lambda _: self.show_day_interface()
        )
        chat_container = ft.Container(
            content=self.chat_messages,
            width=self.page.width * 0.8,
            height=self.page.height * 0.6,
            border=ft.border.all(2, ft.colors.RED),
            padding=10
        )
        input_row = ft.Row(
            [
                self.chat_input,
                self.chat_btn
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            width=self.page.width * 0.8
        )
        self.page.add(
            ft.Column(
                [
                    ft.Row([back_button], alignment=ft.MainAxisAlignment.START),
                    ft.Text("Чат обсуждения", style=r_style),
                    chat_container,
                    ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                    input_row
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.ALWAYS
            )
        )
        self.page.update()

    def show_day_interface(self):
        self.clear_page()
        self.current_view = "day"
        self.page.controls.extend(self.day_phase_controls)
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
        self.current_view = "game_over"
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        role_list = ft.ListView(expand=True)
        for name, role in roles.items():
            role_list.controls.append(
                ft.Text(f"{name}: {jsonroles[role]}", style=w_style)
            )
        button = ft.OutlinedButton(
            content=ft.Text("Вернуться в лобби", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            on_click=lambda e: self.page.run_task(self._return_to_lobby, e),
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

    async def _return_to_lobby(self, e):
        await self.network.close_ws()
        self.show_menu()

    def show_game_cancelled(self):
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        button = ft.OutlinedButton(
            content=ft.Text("Вернуться в лобби", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            on_click=lambda e: self.page.run_task(self._return_to_lobby, e),  # Исправлено здесь
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            )
        )
        button.on_hover = lambda e: self.handle_hover(button, e)
        self.page.add(
            ft.Column(
                [
                    ft.Text("Игра отменена из-за недостатоного количества игроков!", style=r_style),
                    button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def show_menu(self):
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        title=ft.Text("ДОБРО ПОЖАЛОВАТЬ В МАФИЮ!", style=r_style)
        connect_button = ft.OutlinedButton(
            content=ft.Text("Подключиться к игре", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            on_click = lambda e: self.show_connect_view(),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            )
        )
        connect_button.on_hover = lambda e: self.handle_hover(connect_button, e)
        rules_button = ft.OutlinedButton(
            content=ft.Text("Правила игры", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            on_click=lambda e: self.show_rules(),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            )
        )
        rules_button.on_hover = lambda e: self.handle_hover(rules_button, e)
        exit_button = ft.OutlinedButton(
            content=ft.Text("Выйти", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            on_click=lambda e: self.close_app(),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            )
        )
        exit_button.on_hover = lambda e: self.handle_hover(exit_button, e)
        self.page.controls.append(title)
        self.page.controls.append(connect_button)
        self.page.controls.append(rules_button)
        self.page.controls.append(exit_button)
        self.page.update()

    def show_rules(self):
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                                     fit=ft.ImageFit.COVER)
        )
        back_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            icon_color=ft.colors.WHITE,
            on_click=lambda _: self.show_menu()
        )
        rules_text = ft.Text(jsonroles['rules'], style=l_r_style, text_align=TextAlign.JUSTIFY)
        rules=ft.Container(
            content=rules_text,
            width=0.95 * self.page.window.width,
            alignment=ft.alignment.center,
            expand=True)
        self.page.add(
            ft.Column(
                [
                    ft.Row([back_button], alignment=ft.MainAxisAlignment.START),
                    rules
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.ALWAYS
            )
        )
        self.page.update()

    def close_app(self, event=None):
        if self.page:
            self.page.window.close()
            self.page.update()

    def show_connection_error(self):
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(
                src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                fit=ft.ImageFit.COVER
            )
        )
        error_text = ft.Text("Кажется, сервер недоступен. Повторите попытку позже!", style=r_style)
        back_button = ft.OutlinedButton(
            content=ft.Text("Вернуться в меню", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            on_click=lambda e: self.show_menu(),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            )
        )
        back_button.on_hover = lambda e: self.handle_hover(back_button, e)

        self.page.add(
            ft.Column(
                [
                    error_text,
                    back_button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def show_server_disconnected(self):
        self.clear_page()
        self.page.decoration = ft.BoxDecoration(
            image=ft.DecorationImage(
                src="/Users/marialazarevic/Downloads/MAFIA DE Wallpapers black suit-2.jpg",
                fit=ft.ImageFit.COVER
            )
        )
        error_text = ft.Text("Соединение с сервером потеряно!", style=r_style)
        back_button = ft.OutlinedButton(
            content=ft.Text("Вернуться в меню", font_family="Ebbe", size=26, color=ft.colors.WHITE),
            on_click=lambda e: self.show_menu(),
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, ft.colors.WHITE)
            ))
        back_button.on_hover = lambda e: self.handle_hover(back_button, e)
        self.page.add(
            ft.Column(
                [
                    error_text,
                    back_button
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        self.page.update()
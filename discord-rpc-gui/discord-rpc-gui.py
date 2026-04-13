#!/usr/bin/env python3
"""
Discord Rich Presence GUI - Interface gráfica para linux-discord-rich-presence
Permite configurar e gerenciar o Rich Presence do Discord sem usar terminal.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, Pango
import json
import os
import subprocess
import signal
import sys

CONFIG_DIR = os.path.expanduser("~/.config/linux-discord-rich-presence")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
BINARY_NAME = "linux-discord-rich-presence"

# Tentar achar o binário
BINARY_PATH = None
for p in [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), BINARY_NAME),
    f"/usr/bin/{BINARY_NAME}",
    f"/usr/local/bin/{BINARY_NAME}",
]:
    if os.path.isfile(p) and os.access(p, os.X_OK):
        BINARY_PATH = p
        break

DEFAULT_CONFIG = [{
    "application_id": 0,
    "state": None,
    "details": None,
    "large_image": None,
    "small_image": None,
    "start_timestamp": None,
    "end_timestamp": None,
    "buttons": [],
    "party": None
}]

CSS = b"""
window {
    background-color: #2b2d31;
}
.header-bar {
    background-color: #1e1f22;
    padding: 12px 16px;
}
.title-label {
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
}
.subtitle-label {
    color: #b5bac1;
    font-size: 12px;
}
.status-running {
    color: #23a559;
    font-size: 13px;
    font-weight: bold;
}
.status-stopped {
    color: #f23f43;
    font-size: 13px;
    font-weight: bold;
}
.main-content {
    padding: 16px;
}
.section-title {
    color: #b5bac1;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
}
.field-label {
    color: #b5bac1;
    font-size: 13px;
}
.field-entry {
    background-color: #1e1f22;
    color: #dbdee1;
    border: 1px solid #3f4147;
    border-radius: 4px;
    padding: 8px 12px;
    font-size: 14px;
    min-height: 20px;
}
.field-entry:focus {
    border-color: #5865f2;
}
.btn-start {
    background-color: #23a559;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
    min-height: 20px;
}
.btn-start:hover {
    background-color: #1a7d41;
}
.btn-stop {
    background-color: #f23f43;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
    min-height: 20px;
}
.btn-stop:hover {
    background-color: #c9303b;
}
.btn-save {
    background-color: #5865f2;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
    min-height: 20px;
}
.btn-save:hover {
    background-color: #4752c4;
}
.btn-secondary {
    background-color: #4e5058;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 13px;
    min-height: 18px;
}
.btn-secondary:hover {
    background-color: #6d6f78;
}
.separator {
    background-color: #3f4147;
    min-height: 1px;
}
.card {
    background-color: #313338;
    border-radius: 8px;
    padding: 16px;
}
.preview-card {
    background-color: #232428;
    border-radius: 8px;
    padding: 16px;
    border: 1px solid #3f4147;
}
.preview-title {
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
}
.preview-text {
    color: #b5bac1;
    font-size: 13px;
}
.log-view {
    background-color: #1e1f22;
    color: #b5bac1;
    font-family: monospace;
    font-size: 12px;
    border: 1px solid #3f4147;
    border-radius: 4px;
    padding: 8px;
}
.tooltip-label {
    color: #949ba4;
    font-size: 11px;
    font-style: italic;
}
"""


class DiscordRPCGui(Gtk.Window):
    def __init__(self):
        super().__init__(title="Discord Rich Presence")
        self.set_default_size(560, 680)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.process = None
        self.log_lines = []

        # Aplicar CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Garantir diretório de config
        os.makedirs(CONFIG_DIR, exist_ok=True)

        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.get_style_context().add_class("header-bar")

        header_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(label="Discord Rich Presence", xalign=0)
        title.get_style_context().add_class("title-label")
        header_left.pack_start(title, False, False, 0)

        self.status_label = Gtk.Label(label="⬤ Parado", xalign=0)
        self.status_label.get_style_context().add_class("status-stopped")
        header_left.pack_start(self.status_label, False, False, 0)
        header.pack_start(header_left, True, True, 0)

        # Botões do header
        header_btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self.btn_start = Gtk.Button(label="▶ Iniciar")
        self.btn_start.get_style_context().add_class("btn-start")
        self.btn_start.connect("clicked", self.on_start)
        header_btns.pack_start(self.btn_start, False, False, 0)

        self.btn_stop = Gtk.Button(label="■ Parar")
        self.btn_stop.get_style_context().add_class("btn-stop")
        self.btn_stop.connect("clicked", self.on_stop)
        self.btn_stop.set_sensitive(False)
        header_btns.pack_start(self.btn_stop, False, False, 0)

        header.pack_end(header_btns, False, False, 0)
        main_box.pack_start(header, False, False, 0)

        # Scrollable content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_box.pack_start(scrolled, True, True, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.get_style_context().add_class("main-content")
        scrolled.add(content)

        # === SEÇÃO: Application ID ===
        content.pack_start(self._section("APLICAÇÃO DISCORD"), False, False, 0)

        app_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        app_card.get_style_context().add_class("card")

        self.entry_app_id = self._labeled_entry(
            app_card, "Application ID",
            "ID numérico do Discord Developer Portal (obrigatório)"
        )
        content.pack_start(app_card, False, False, 0)

        # === SEÇÃO: Textos ===
        content.pack_start(self._section("TEXTOS DA PRESENÇA"), False, False, 0)

        text_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        text_card.get_style_context().add_class("card")

        self.entry_details = self._labeled_entry(
            text_card, "Details (linha de cima)",
            "Ex: Jogando Minecraft"
        )
        self.entry_state = self._labeled_entry(
            text_card, "State (linha de baixo)",
            "Ex: Survival Mode"
        )
        content.pack_start(text_card, False, False, 0)

        # === SEÇÃO: Imagens ===
        content.pack_start(self._section("IMAGENS"), False, False, 0)

        img_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        img_card.get_style_context().add_class("card")

        self.entry_large_img = self._labeled_entry(
            img_card, "Imagem Grande (key)",
            "Nome da imagem no Developer Portal"
        )
        self.entry_large_text = self._labeled_entry(
            img_card, "Texto ao passar o mouse (imagem grande)",
            "Texto que aparece ao passar o mouse"
        )

        sep = Gtk.Separator()
        sep.get_style_context().add_class("separator")
        img_card.pack_start(sep, False, False, 4)

        self.entry_small_img = self._labeled_entry(
            img_card, "Imagem Pequena (key)",
            "Nome da imagem pequena no Developer Portal"
        )
        self.entry_small_text = self._labeled_entry(
            img_card, "Texto ao passar o mouse (imagem pequena)",
            "Texto que aparece ao passar o mouse"
        )
        content.pack_start(img_card, False, False, 0)

        # === SEÇÃO: Botões ===
        content.pack_start(self._section("BOTÕES (máximo 2)"), False, False, 0)

        btn_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        btn_card.get_style_context().add_class("card")

        self.entry_btn1_label = self._labeled_entry(btn_card, "Botão 1 - Texto", "Ex: Meu Site")
        self.entry_btn1_url = self._labeled_entry(btn_card, "Botão 1 - URL", "Ex: https://meusite.com")

        sep2 = Gtk.Separator()
        sep2.get_style_context().add_class("separator")
        btn_card.pack_start(sep2, False, False, 4)

        self.entry_btn2_label = self._labeled_entry(btn_card, "Botão 2 - Texto", "")
        self.entry_btn2_url = self._labeled_entry(btn_card, "Botão 2 - URL", "")
        content.pack_start(btn_card, False, False, 0)

        # === SEÇÃO: Party ===
        content.pack_start(self._section("PARTY (grupo)"), False, False, 0)

        party_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        party_card.get_style_context().add_class("card")

        party_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.entry_party_cur = self._labeled_entry(party_left, "Tamanho atual", "Ex: 1")
        party_card.pack_start(party_left, True, True, 0)

        party_right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.entry_party_max = self._labeled_entry(party_right, "Tamanho máximo", "Ex: 5")
        party_card.pack_start(party_right, True, True, 0)

        content.pack_start(party_card, False, False, 0)

        # === SEÇÃO: Opções ===
        content.pack_start(self._section("OPÇÕES"), False, False, 0)

        opt_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        opt_card.get_style_context().add_class("card")

        self.chk_show_elapsed = Gtk.CheckButton(label="Mostrar tempo decorrido (elapsed)")
        self.chk_show_elapsed.set_active(False)
        lbl = self.chk_show_elapsed.get_child()
        if lbl:
            lbl.set_markup('<span color="#b5bac1">Mostrar tempo decorrido (elapsed)</span>')
        opt_card.pack_start(self.chk_show_elapsed, False, False, 0)

        content.pack_start(opt_card, False, False, 0)

        # === Botão salvar ===
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)

        btn_save = Gtk.Button(label="💾 Salvar Configuração")
        btn_save.get_style_context().add_class("btn-save")
        btn_save.connect("clicked", self.on_save)
        btn_box.pack_start(btn_save, False, False, 0)

        btn_save_start = Gtk.Button(label="💾 Salvar e Iniciar")
        btn_save_start.get_style_context().add_class("btn-start")
        btn_save_start.connect("clicked", self.on_save_and_start)
        btn_box.pack_start(btn_save_start, False, False, 0)

        content.pack_start(btn_box, False, False, 8)

        # === Preview ===
        content.pack_start(self._section("PRÉ-VISUALIZAÇÃO"), False, False, 0)
        self.preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.preview_box.get_style_context().add_class("preview-card")
        self._build_preview()
        content.pack_start(self.preview_box, False, False, 0)

        # Atualizar preview ao editar
        for entry in [self.entry_app_id, self.entry_details, self.entry_state,
                       self.entry_large_img, self.entry_large_text,
                       self.entry_small_img, self.entry_small_text,
                       self.entry_btn1_label, self.entry_btn1_url,
                       self.entry_btn2_label, self.entry_btn2_url,
                       self.entry_party_cur, self.entry_party_max]:
            entry.connect("changed", lambda *_: self._build_preview())

        self.chk_show_elapsed.connect("toggled", lambda *_: self._build_preview())

        # Carregar config existente
        self._load_config()

        # Fechar = minimizar para segundo plano se processo estiver rodando
        self.connect("delete-event", self.on_close)
        self.show_all()

    def _section(self, text):
        label = Gtk.Label(label=text, xalign=0)
        label.get_style_context().add_class("section-title")
        return label

    def _labeled_entry(self, parent, label_text, placeholder):
        lbl = Gtk.Label(label=label_text, xalign=0)
        lbl.get_style_context().add_class("field-label")
        parent.pack_start(lbl, False, False, 0)

        entry = Gtk.Entry()
        entry.get_style_context().add_class("field-entry")
        if placeholder:
            entry.set_placeholder_text(placeholder)
        parent.pack_start(entry, False, False, 0)
        return entry

    def _build_preview(self):
        # Limpar preview
        for child in self.preview_box.get_children():
            self.preview_box.remove(child)

        title = Gtk.Label(xalign=0)
        title.set_markup('<span color="#ffffff" font_weight="bold" size="medium">Preview da Presença</span>')
        self.preview_box.pack_start(title, False, False, 0)

        details = self.entry_details.get_text().strip() or "(sem details)"
        state = self.entry_state.get_text().strip() or "(sem state)"
        large = self.entry_large_img.get_text().strip()
        small = self.entry_small_img.get_text().strip()
        elapsed = self.chk_show_elapsed.get_active()

        info_text = f'<span color="#b5bac1" size="small">'
        if large:
            info_text += f'🖼 <span color="#949ba4">{large}</span>  '
        if small:
            info_text += f'🔹 <span color="#949ba4">{small}</span>  '
        info_text += '</span>'

        if large or small:
            info_lbl = Gtk.Label(xalign=0)
            info_lbl.set_markup(info_text)
            self.preview_box.pack_start(info_lbl, False, False, 2)

        details_lbl = Gtk.Label(xalign=0)
        details_lbl.set_markup(f'<span color="#dcddde" size="medium">{GLib.markup_escape_text(details)}</span>')
        self.preview_box.pack_start(details_lbl, False, False, 1)

        state_lbl = Gtk.Label(xalign=0)
        state_lbl.set_markup(f'<span color="#b5bac1" size="small">{GLib.markup_escape_text(state)}</span>')
        self.preview_box.pack_start(state_lbl, False, False, 1)

        if elapsed:
            elapsed_lbl = Gtk.Label(xalign=0)
            elapsed_lbl.set_markup('<span color="#949ba4" size="small">⏱ 00:00 elapsed</span>')
            self.preview_box.pack_start(elapsed_lbl, False, False, 1)

        # Botões preview
        btn1_label = self.entry_btn1_label.get_text().strip()
        btn2_label = self.entry_btn2_label.get_text().strip()
        if btn1_label or btn2_label:
            btn_preview = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            if btn1_label:
                b1 = Gtk.Label()
                b1.set_markup(f'<span color="#5865f2" size="small">[{GLib.markup_escape_text(btn1_label)}]</span>')
                btn_preview.pack_start(b1, False, False, 0)
            if btn2_label:
                b2 = Gtk.Label()
                b2.set_markup(f'<span color="#5865f2" size="small">[{GLib.markup_escape_text(btn2_label)}]</span>')
                btn_preview.pack_start(b2, False, False, 0)
            self.preview_box.pack_start(btn_preview, False, False, 2)

        # Party preview
        cur = self.entry_party_cur.get_text().strip()
        mx = self.entry_party_max.get_text().strip()
        if cur and mx:
            party_lbl = Gtk.Label(xalign=0)
            party_lbl.set_markup(f'<span color="#949ba4" size="small">👥 {cur} de {mx}</span>')
            self.preview_box.pack_start(party_lbl, False, False, 1)

        self.preview_box.show_all()

    def _build_config(self):
        """Monta o JSON de configuração."""
        app_id_text = self.entry_app_id.get_text().strip()
        try:
            app_id = int(app_id_text)
        except ValueError:
            app_id = 0

        config = {"application_id": app_id}

        state = self.entry_state.get_text().strip()
        details = self.entry_details.get_text().strip()
        if state:
            config["state"] = state
        if details:
            config["details"] = details

        large_key = self.entry_large_img.get_text().strip()
        large_text = self.entry_large_text.get_text().strip()
        if large_key:
            config["large_image"] = {"key": large_key}
            if large_text:
                config["large_image"]["text"] = large_text

        small_key = self.entry_small_img.get_text().strip()
        small_text = self.entry_small_text.get_text().strip()
        if small_key:
            config["small_image"] = {"key": small_key}
            if small_text:
                config["small_image"]["text"] = small_text

        if self.chk_show_elapsed.get_active():
            import time
            config["start_timestamp"] = int(time.time())

        buttons = []
        b1_label = self.entry_btn1_label.get_text().strip()
        b1_url = self.entry_btn1_url.get_text().strip()
        if b1_label and b1_url:
            buttons.append({"label": b1_label, "url": b1_url})
        b2_label = self.entry_btn2_label.get_text().strip()
        b2_url = self.entry_btn2_url.get_text().strip()
        if b2_label and b2_url:
            buttons.append({"label": b2_label, "url": b2_url})
        if buttons:
            config["buttons"] = buttons

        cur = self.entry_party_cur.get_text().strip()
        mx = self.entry_party_max.get_text().strip()
        if cur and mx:
            try:
                config["party"] = [int(cur), int(mx)]
            except ValueError:
                pass

        return [config]

    def _load_config(self):
        """Carrega config do arquivo JSON."""
        if not os.path.isfile(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            if not isinstance(data, list) or len(data) == 0:
                return
            c = data[0]
            self.entry_app_id.set_text(str(c.get("application_id", "")))
            self.entry_state.set_text(c.get("state", "") or "")
            self.entry_details.set_text(c.get("details", "") or "")

            large = c.get("large_image")
            if large and isinstance(large, dict):
                self.entry_large_img.set_text(large.get("key", ""))
                self.entry_large_text.set_text(large.get("text", "") or "")

            small = c.get("small_image")
            if small and isinstance(small, dict):
                self.entry_small_img.set_text(small.get("key", ""))
                self.entry_small_text.set_text(small.get("text", "") or "")

            if c.get("start_timestamp"):
                self.chk_show_elapsed.set_active(True)

            buttons = c.get("buttons", [])
            if len(buttons) >= 1:
                self.entry_btn1_label.set_text(buttons[0].get("label", ""))
                self.entry_btn1_url.set_text(buttons[0].get("url", ""))
            if len(buttons) >= 2:
                self.entry_btn2_label.set_text(buttons[1].get("label", ""))
                self.entry_btn2_url.set_text(buttons[1].get("url", ""))

            party = c.get("party")
            if party and isinstance(party, list) and len(party) == 2:
                self.entry_party_cur.set_text(str(party[0]))
                self.entry_party_max.set_text(str(party[1]))

        except Exception as e:
            print(f"Erro ao carregar config: {e}")

    def on_save(self, _btn=None):
        config = self._build_config()
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            self._show_toast("Configuração salva!")
            return True
        except Exception as e:
            self._show_error(f"Erro ao salvar: {e}")
            return False

    def on_save_and_start(self, btn):
        if self.on_save():
            self.on_start(btn)

    def on_start(self, _btn):
        if self.process and self.process.poll() is None:
            return

        if not BINARY_PATH:
            self._show_error(
                f"Binário '{BINARY_NAME}' não encontrado!\n\n"
                "Coloque o binário compilado na mesma pasta deste script\n"
                "ou instale em /usr/bin/"
            )
            return

        if not os.path.isfile(CONFIG_FILE):
            self.on_save()

        try:
            self.process = subprocess.Popen(
                [BINARY_PATH, "--config", CONFIG_FILE],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            self.status_label.set_text("⬤ Rodando")
            self.status_label.get_style_context().remove_class("status-stopped")
            self.status_label.get_style_context().add_class("status-running")
            self.btn_start.set_sensitive(False)
            self.btn_stop.set_sensitive(True)

            # Monitorar processo
            GLib.timeout_add(2000, self._check_process)

        except Exception as e:
            self._show_error(f"Erro ao iniciar: {e}")

    def on_stop(self, _btn):
        if self.process and self.process.poll() is None:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            self.process = None

        self.status_label.set_text("⬤ Parado")
        self.status_label.get_style_context().remove_class("status-running")
        self.status_label.get_style_context().add_class("status-stopped")
        self.btn_start.set_sensitive(True)
        self.btn_stop.set_sensitive(False)

    def _check_process(self):
        if self.process and self.process.poll() is not None:
            self.on_stop(None)
            return False
        return self.process is not None

    def on_close(self, widget, event):
        if self.process and self.process.poll() is None:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.NONE,
                text="O que deseja fazer?"
            )
            dialog.format_secondary_text(
                "O Rich Presence está rodando. Você pode minimizar para "
                "manter rodando em segundo plano ou parar tudo e fechar."
            )
            dialog.add_button("Minimizar (manter rodando)", 1)
            dialog.add_button("Parar e Fechar", 2)
            dialog.add_button("Cancelar", 3)

            response = dialog.run()
            dialog.destroy()

            if response == 1:
                self.iconify()
                return True
            elif response == 2:
                self.on_stop(None)
                Gtk.main_quit()
                return False
            else:
                return True
        else:
            Gtk.main_quit()
            return False

    def _show_toast(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def _show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Erro"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


def main():
    # Tratar Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = DiscordRPCGui()
    Gtk.main()


if __name__ == "__main__":
    main()

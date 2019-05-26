from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem, TabbedPanelHeader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from flexproto import flexclient
from kivy.uix.textinput import TextInput
from threading import Thread
from binascii import hexlify, unhexlify
from kivy.clock import Clock
import kivy
from time import sleep
import logging
from kivy.logger import Logger
# logger = kivy.logger.logging
# logger.level = logging.DEBUG
from kivy.config import Config
Config.set('kivy', 'log_level', 'debug')
Config.set('kivy', 'log_enable', 0)
Config.write()
debug = Logger.debug


class MainWin(App):
    def build(self):
        self.master_panel = TabbedPanel(do_default_tab=False)
        self.users = dict()
        # users data structure:
        # users[key] = {"tab":tab, "outbox":outbox, "inbox", inbox}
        # set up the new connections tab
        connect_tab = TabbedPanelHeader(text="Connect")
        connectLayout = BoxLayout(padding=10, orientation="vertical")
        connect_label = Button(text="Connect", font_size="20sp")
        connectLayout.add_widget(connect_label)

        serverTextbox = TextInput(text="127.0.0.1")
        serverTextbox.multiline = False

        def on_enter(instance):  # callback for return key in the hostname box.
            self.flex = flexclient(ip=instance.text)
            self.username = self.flex.username
            self.flex.got_message_callback = self.got_message_callback
            self.flex.got_roster_callback = self.got_roster_callback

            self.master_panel.switch_to(self.roster)
            self.build_roster()
            
            # self.flex.got_roster_callback = self.build_roster

        serverTextbox.bind(on_text_validate=on_enter)
        connectLayout.add_widget(serverTextbox)

        usernameTextbox = TextInput(text="")
        usernameTextbox.multiline = False
        connectLayout.add_widget(usernameTextbox)

        connect_tab.content = connectLayout
        self.master_panel.add_widget(connect_tab)

        # roster tab setup
        tab_header = TabbedPanelHeader(text="Roster")

        self.rosterLayout = BoxLayout(padding=10, orientation="vertical")
        title_label = Label(text="Hello world", font_size="20sp")
        self.rosterLayout.add_widget(title_label)
        tab_header.content = self.rosterLayout
        self.roster = tab_header
        self.master_panel.add_widget(tab_header)

        return self.master_panel

    def build_roster(self):
        self.rosterLayout.clear_widgets()
        for user in self.flex.roster:
            pub_key = user["key"]  # str(unhexlify(name['key']), encoding="utf-8")
            try:
                alias = user["aliases"][0]
            except IndexError:
                alias = "###"
            if pub_key not in self.users.keys():
                self.users[pub_key] = {"alias": alias}
            button = Button(text=alias)  # + "\n" + str(pub_key))
            button.bind(on_press=self.roster_click_callback)
            self.rosterLayout.add_widget(button)

    def roster_click_callback(self, instance):
        self.newChatTab(self.alias_to_key(instance.text))

    def alias_to_key(self, target):
        # find the key, given an alias. #TODO: this is O(n^slow) fix it.
        key = None
        for k in self.users.keys():
            alias = self.users[k].get("alias")
            debug(
                f"k: {k} alias:{alias} target: {target} l:{len(target)} {len(alias)} || {alias==target}"
            )
            if alias == target:
                return k

    def newChatTab(self, key):
        # setup a new tab, or switch to required tab.
        debug("newChatTab key:")
        debug(key)
        if (
            self.users.get(key, None) is None
        ):  # FIXME: dies when recieving messages from unknown users.
            debug("newChatTab users.get[key]: ")
            debug(self.users.keys())
            self.flex.request_roster()
            self.build_roster()
        debug("key error key:")
        debug(key)
        debug(" " + str(self.users.keys()))
        if self.users[key].get("tab", None) is not None:
            self.master_panel.switch_to(
                self.users[key]["tab"]
            )  # this, or master_panel.tab_list[0]?
        else:  # build new tab, then swap focus.
            debug(self.flex.roster)
            chat_tab = TabbedPanelHeader(text=self.users[key]["alias"])
            chatLayout = BoxLayout(padding=10, orientation="vertical")
            chatOutput = TextInput(text="")
            chatLayout.add_widget(chatOutput)
            chatInput = TextInput(text="", size_hint=(1, 0.1))
            chatInput.multiline = False

            def set_chatInput_focus(_):
                chatInput.focus = True

            def on_enter(instance):  # callback for return key in the hostname box.
                self.flex.send_message(message=chatInput.text, to=key)
                self.users[key]["outbox"].text += "\n<<<" + chatInput.text
                self.users[key]["inbox"].text = ""

                Clock.schedule_once(set_chatInput_focus, 0.1)

            chatInput.bind(on_text_validate=on_enter)
            chatLayout.add_widget(chatInput)

            chat_tab.content = chatLayout
            self.users[key]["tab"] = chat_tab
            self.users[key]["inbox"] = chatInput
            self.users[key]["outbox"] = chatOutput
            self.master_panel.add_widget(chat_tab)
            self.master_panel.switch_to(self.users[key]["tab"])
            Clock.schedule_once(set_chatInput_focus, 0.1)

    msgqueue = list()

    def got_message_callback(self, d_data):
        key_from = unhexlify(
            d_data["from"]
        )  # str(unhexlify(d_data['from']), encoding="utf-8")
        debug("got_message_callback: " + str(d_data))
        if self.users.get(key_from, None) is not None:
            self.newChatTab(key_from)
            self.users[key_from]["outbox"].text += "\n>>>" + d_data["msg"]
        else:
            self.msgqueue.append(d_data)

    def got_roster_callback(self):
        #self.flex.got_roster_callback()
        debug("got_roster_callback")
        self.build_roster()
        for msg in self.msgqueue:
            key_from = unhexlify(msg["from"])
            if self.users.get(key_from, None) is not None:
                debug('calling newChatTab:' + str(key_from))
                self.newChatTab(key_from)
                self.users[key_from]["outbox"].text += "\n>>>" + msg["msg"]
                self.msgqueue.remove(msg)


MainWin().run()

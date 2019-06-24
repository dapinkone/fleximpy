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

Config.set("kivy", "log_level", "debug")
Config.set("kivy", "log_enable", 0)
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

        def on_enter(instance):  # callback for return key in the hostname box.
            self.flex = flexclient(
                ip=serverTextbox.text, username=self.usernameTextbox.text
            )
            self.username = self.usernameTextbox.text
            self.flex.got_message_callback = self.got_message_callback
            self.flex.got_roster_callback = self.got_roster_callback
            self.flex.got_status_callback = self.got_status_callback

            self.master_panel.switch_to(self.rosterTab)
            self.load_roster_tab()

            # self.flex.got_roster_callback = self.build_roster
        serverSubLayout = BoxLayout(orientation="horizontal")
        serverSubLayout.add_widget(Label(text="Hostname:"))
        serverTextbox = TextInput(text="127.0.0.1")
        serverTextbox.multiline = False
        serverTextbox.bind(on_text_validate=on_enter)
        serverSubLayout.add_widget(serverTextbox)
        connectLayout.add_widget(serverSubLayout)

        usernameSubLayout = BoxLayout(orientation="horizontal")
        usernameSubLayout.add_widget(Label(text="Username:"))
        self.usernameTextbox = TextInput(text="", on_text_validate=on_enter)
        self.usernameTextbox.multiline = False
        usernameSubLayout.add_widget(self.usernameTextbox)
        connectLayout.add_widget(usernameSubLayout)

        connect_label = Button(text="Connect", font_size="20sp", on_press=on_enter)
        connectLayout.add_widget(connect_label)

        connect_tab.content = connectLayout
        self.master_panel.add_widget(connect_tab)



        # roster tab setup
        tab_header = TabbedPanelHeader(text="Roster")

        self.rosterTabLayout = BoxLayout(padding=10, orientation="vertical")
        title_label = Label(text="Hello world", font_size="20sp")
        self.rosterTabLayout.add_widget(title_label)
        tab_header.content = self.rosterTabLayout
        self.master_panel.add_widget(tab_header)
        self.rosterTab = tab_header
        return self.master_panel

    def load_roster_tab(self):
        self.rosterTabLayout.clear_widgets()
        debug("Clearing Widgets")
        for pub_key in self.flex.roster.keys():
            alias = self.flex.roster.get(pub_key, {}).get("alias", None)
            if alias is None:
                alias = "###"
            if pub_key not in self.users:
                self.users[pub_key] = dict()
            self.users[pub_key].update({"alias": alias})

            debug("new button: " + alias)
            button = Button(text=alias)
            if self.users.get(pub_key, {}).get("status") == -10:
                button.color = [0.41, 0.42, 0.74, 1]
            button.bind(on_press=self.roster_click_callback)
            self.users[pub_key].update({"rosterButton": button})
            debug("button made for " + alias)
            self.rosterTabLayout.add_widget(button)

    def roster_click_callback(self, instance):
        self.newChatTab(self.alias_to_key(instance.text))

    def alias_to_key(self, target):
        # find the key, given an alias. #TODO: this is O(n^slow) fix it.
        for k in self.users.keys():
            alias = self.users[k].get("alias")
            # debug(
            #    f"k: {k} alias:{alias} target: {target} l:{len(target)} {len(alias)} || {alias==target}"
            # )
            if alias == target:
                return k

    def newChatTab(self, key):
        # setup a new tab, or switch to required tab.
        debug("newChatTab key:")
        debug(key)
        if self.users.get(key, None) is None:
            debug("newChatTab users.get[key]: ")
            debug(self.users.keys())
            self.flex.request_roster()
            self.load_roster_tab()
        # debug("key error key:")
        # debug(key)
        # debug(" " + str(self.users.keys()))
        if self.users[key].get("tab", None) is not None:
            self.master_panel.switch_to(
                self.users[key]["tab"]
            )  # this, or master_panel.tab_list[0]?
        else:  # build new tab, then swap focus.
            # debug(self.flex.roster)
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
        alias = None
        if d_data["flags"]:
            flags = d_data["flags"]
            try:
                for flag, val in (s.split("=") for s in flags):
                    if flag == "alias":
                        alias = val
            except ValueError:
                debug("ERROR: malformed flags: " + str(flags))
        d_data['to'] = unhexlify(d_data['to'])
        d_data['from']=unhexlify(d_data['from'])
        debug("got_message_callback: " + str(d_data))
        if self.users.get(key_from, None) is None:
            self.users[key_from] = {"alias": alias}

        self.newChatTab(key_from)
        self.users[key_from]["outbox"].text += "\n" + alias + ">>>" + d_data["msg"]
        # else:
        #   self.msgqueue.append(d_data)

    def got_roster_callback(self):
        # self.flex.got_roster_callback()
        debug("got_roster_callback")
        self.load_roster_tab()
        for msg in self.msgqueue:
            key_from = unhexlify(msg["from"])
            if self.users.get(key_from, None) is not None:
                debug("calling newChatTab:" + str(key_from))
                self.newChatTab(key_from)
                self.users[key_from]["outbox"].text += "\n>>>" + msg["msg"]
                self.msgqueue.remove(msg)
            else:
                debug("174 user not found:" + key_from)
                self.flex.request_roster()  # strangers about.

    def got_status_callback(self, d_data):
        pub_key = d_data["payload"]
        self.users[pub_key] = self.users.get(pub_key, {})
        # if d_data['status'] == -10:
        #     user_button._label.options['color']=[255,255,255,1]
        # elif d_data['status'] == 10:
        #     user_button._label.options['color']=[255,0,0,1]
        self.users[pub_key].update({"status": d_data["status"]})
        if d_data["status"] == -10:
            self.users[pub_key].get("RosterButton")
        self.load_roster_tab()


MainWin().run()

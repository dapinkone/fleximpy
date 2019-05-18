from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem, TabbedPanelHeader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from flexproto import flexclient
from kivy.uix.textinput import TextInput
from threading import Thread
from binascii import hexlify, unhexlify


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
            self.flex.got_message_callback = self.got_message_callback
            for name in self.flex.roster:
                pub_key = name["key"]  # str(unhexlify(name['key']), encoding="utf-8")
                print("roster name:" + str(name))
                try:
                    alias = name["aliases"][0]
                except IndexError:
                    alias = "###"
                if pub_key not in self.users.keys():
                    self.users[pub_key] = {"alias": alias}
                button = Button(text=alias)
                button.bind(on_press=self.roster_click_callback)
                self.rosterLayout.add_widget(button)
            self.master_panel.switch_to(self.roster)

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

    def roster_click_callback(self, instance):
        self.newChatTab(instance.text)

    def newChatTab(self, target: str):
        # setup a new tab, or switch to required tab.

        # find the key, given an alias. #TODO: this is O(n^slow) fix it.
        key = None
        for k in self.users.keys():
            alias = self.users[k].get("alias")
            print(f"k: {k} alias:{alias}")
            if alias:
                key = k
        # key = [k for k in self.users.keys() if self.users[k].get("alias",None)==target][0]
        if self.users[key].get("tab", None) is not None:
            self.master_panel.switch_to(
                self.users[key]["tab"]
            )  # this, or master_panel.tab_list[0]?
        else:  # build new tab, then swap focus.
            print(self.flex.roster)
            chat_tab = TabbedPanelHeader(text=self.users[key]["alias"])
            chatLayout = BoxLayout(padding=10, orientation="vertical")
            chatOutput = TextInput(text="")
            chatLayout.add_widget(chatOutput)
            chatInput = TextInput(text="", size_hint=(None, 0.2))
            chatInput.multiline = False

            def on_enter(instance):  # callback for return key in the hostname box.
                print("sending msg to: " + target)
                self.flex.send_message(message=chatInput.text, to=key)
                self.users[key]["outbox"].text += "\n<<<" + chatInput.text
                self.users[key]["inbox"].text = ""
                

            chatInput.bind(on_text_validate=on_enter)
            chatLayout.add_widget(chatInput)

            chat_tab.content = chatLayout
            self.users[key]["tab"] = chat_tab
            self.users[key]["inbox"] = chatInput
            self.users[key]["outbox"] = chatOutput
            self.master_panel.add_widget(chat_tab)
            self.master_panel.switch_to(self.users[key]["tab"])

    def got_message_callback(self, d_data):
        key_from = unhexlify(
            d_data["from"]
        )  # str(unhexlify(d_data['from']), encoding="utf-8")
        print("got_message_callback: " + str(d_data))
        self.newChatTab(key_from)
        self.users[key_from]["outbox"].text += "\n>>>" + d_data["msg"]


MainWin().run()

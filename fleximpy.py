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
        connect_label = Label(text=u"Connect to server:", font_size="20sp")
        connectLayout.add_widget(connect_label)
        
        serverTextbox = TextInput(text="10.20.30.14")
        serverTextbox.multiline = False

        def on_enter(instance):  # callback for return key in the hostname box.
            self.flex = flexclient(ip=instance.text)
            self.flex.got_message_callback = self.got_message_callback
            for name in self.flex.roster:
                pub_key = name["key"]  # str(unhexlify(name['key']), encoding="utf-8")
                try:
                    alias = name["aliases"][0]
                except IndexError:
                    alias = "###"
                if pub_key not in self.users.keys():
                    self.users[pub_key] = {"key": pub_key, "alias": alias}
                button = Button(text=alias)
                button.bind(on_press=self.roster_click_callback)
                self.rosterLayout.add_widget(button)
            self.master_panel.switch_to(self.tabs["Roster"])

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
        title_label = Label(text=u"Hello world", font_size="20sp")
        self.rosterLayout.add_widget(title_label)
        tab_header.content = self.rosterLayout
        self.roster = tab_header
        self.master_panel.add_widget(tab_header)

        return self.master_panel

    def roster_click_callback(self, instance):
        self.newChatTab(instance.text)

    def newChatTab(self, target: str):
        # set up a tab for each target user
        if target in self.users.keys():
            self.master_panel.switch_to(
                self.users[target]["tab"]
            )  # this, or master_panel.tab_list[0]?
        else:  # build new tab, then swap focus.
            chat_tab = TabbedPanelHeader(text=self.users[target]["alias"])
            chatLayout = BoxLayout(padding=10, orientation="horizontal")
            chatOutput = TextInput(text="")
            chatLayout.add_widget(chatOutput)
            chatInput = TextInput(text="", size_hint=(0.2, None))
            chatInput.multiline = False

            def on_enter(instance):  # callback for return key in the hostname box.
                print("sending msg to: " + target)
                self.flex.send_message(message=chatInput.text, to=target)

            chatInput.bind(on_text_validate=on_enter)
            chatLayout.add_widget(chatInput)

            chat_tab.content = chatLayout
            self.users[target]["tab"] = chat_tab
            self.users[target]["inbox"] = chatInput
            self.users[target]["outbox"] = chatOutput
            self.master_panel.add_widget(chat_tab)

    def got_message_callback(self, d_data):
        target = d_data["from"]  # str(unhexlify(d_data['from']), encoding="utf-8")
        self.newChatTab(target)
        self.chatboxes[target].text += "\n>>>" + d_data["msg"]
        pass


MainWin().run()

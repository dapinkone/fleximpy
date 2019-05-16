from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem, TabbedPanelHeader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from flexproto import flexclient
from kivy.uix.textinput import TextInput




class MainWin(App):
    def build(self):
        self.master_panel = TabbedPanel(do_default_tab=False)

        # set up the new connections tab
        connect_tab = TabbedPanelHeader(text="Connect")
        connectLayout = BoxLayout(padding=10, orientation="horizontal")
        connect_label = Label(text=u"Connect to server:", font_size="20sp")
        connectLayout.add_widget(connect_label)
        serverTextbox = TextInput(text="")
        serverTextbox.multiline = False

        def on_enter(instance): # callback for return key in the hostname box.
            self.flex = flexclient(ip=instance.text)

            for name in self.flex.roster:
                button = Button(text="Send Msg to " + str(name[b'aliases'][0]))
                button.bind(on_press=self.roster_click_callback)
                self.rosterLayout.add_widget(button)
            

        serverTextbox.bind(on_text_validate=on_enter)
        connectLayout.add_widget(serverTextbox)

        connect_tab.content = connectLayout
        self.master_panel.add_widget(connect_tab)

        # roster tab setup
        tab_header = TabbedPanelHeader(text="Roster")

        self.rosterLayout = BoxLayout(padding=10, orientation="vertical")
        title_label = Label(text=u"Hello world", font_size="20sp")
        self.rosterLayout.add_widget(title_label)
        tab_header.content = self.rosterLayout
        self.master_panel.add_widget(tab_header)

        return self.master_panel


    def roster_click_callback(self, instance):
        self.newChatTab(instance.text)

    def newChatTab(self, target):
                # set up the new connections tab
            chat_tab = TabbedPanelHeader(text=target)
            chatLayout = BoxLayout(padding=10, orientation="horizontal")
            chat_label = Label(text=u"Connect to server:", font_size="20sp")
            chatLayout.add_widget(chat_label)
            chatTextbox = TextInput(text="")
            chatTextbox.multiline = False

            def on_enter(instance): # callback for return key in the hostname box.
                self.flex.send_message(message="hello?")

            chatTextbox.bind(on_text_validate=on_enter)
            chatLayout.add_widget(chatTextbox)

            chat_tab.content = chatLayout
            self.master_panel.add_widget(chat_tab)

MainWin().run()

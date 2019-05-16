from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem, TabbedPanelHeader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from flexproto import flexclient
from kivy.uix.textinput import TextInput


def callback(instance):
    print("The button <%s> is being pressed" % instance.text)


class MainWin(App):
    def build(self):
        master_panel = TabbedPanel(do_default_tab=False)

        connect_tab = TabbedPanelHeader(text="Connect")
        connectLayout = BoxLayout(padding=10, orientation="horizontal")

        connect_label = Label(text=u"Connect to server:", font_size="20sp")
        connectLayout.add_widget(connect_label)

        serverTextbox = TextInput(text="")
        serverTextbox.multiline = False

        def on_enter(instance):
            self.flex = flexclient(ip=instance.text)

        serverTextbox.bind(on_text_validate=on_enter)
        connectLayout.add_widget(serverTextbox)

        connect_tab.content = connectLayout
        master_panel.add_widget(connect_tab)

        tab_header = TabbedPanelHeader(text="Roster")

        rosterLayout = BoxLayout(padding=10, orientation="vertical")
        title_label = Label(text=u"Hello world", font_size="20sp")
        rosterLayout.add_widget(title_label)
        for b in range(10):
            button = Button(text="Button " + str(b))
            button.bind(on_press=callback)
            rosterLayout.add_widget(button)
        tab_header.content = rosterLayout
        master_panel.add_widget(tab_header)

        return master_panel


class jklClient:
    roster = list()


MainWin().run()

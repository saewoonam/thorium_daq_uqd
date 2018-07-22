
import remi.gui as gui
from remi import start, App
import shm_buffer
import reset
import numpy as np
import threading


buf= shm_buffer.buffer()

class MyApp(App):
    def __init__(self, *args):
        super(MyApp, self).__init__(*args)

    def main(self, name='world'):
        #margin 0px auto allows to center the app to the screen
        wid = gui.VBox(width=300, height=300, margin='0px auto')
        counts_labels = []
        count_lbl = gui.Label('Counts', width='80%', height='20%')
        count_lbl.style['font-size'] = '30px'
        count_lbl.style['margin'] = 'auto'
        for index in range(4):
            lbl = gui.Label('Hello %d!' % index, width='80%', height='20%')
            lbl.style['font-size'] = '30px'
            lbl.style['margin'] = 'auto'
            counts_labels.append(lbl)
        self.counts_labels = counts_labels
        print(counts_labels)
        bt = gui.Button('Get Counts', width=200, height=40)
        bt.style['margin'] = 'auto 50px'
        bt.style['background-color'] = 'green'

        reset_bt = gui.Button('Reset detectors', width=200, height=40)
        reset_bt.style['margin'] = 'auto 50px'

        # setting the listener for the onclick event of the button
        self.npressed = 0

        # bt.set_on_click_listener(self.on_button_pressed, lbl)
        bt.set_on_mousedown_listener(self.on_button_mousedown, lbl)
        bt.set_on_mouseup_listener(self.on_button_mouseup, lbl) 

        reset_bt.set_on_click_listener(self.reset_button_pressed, lbl)

        # appending a widget to another, the first argument is a string key
        wid.append(count_lbl)
        for lbl in counts_labels:
            wid.append(lbl)
        wid.append(bt)
        wid.append(reset_bt)
        self.running = False
        # returning the root widget
        return wid

    # listener function
    def on_button_pressed(self, widget, lbl):
        self.running = not self.running
        if self.running is True:
            threading.Timer(1, self.update_counts, [widget, lbl]).start()
        else:
            widget.style['background-color'] = 'green'
            widget.set_text('Get Counts')

    def update_counts(self, widget, lbl):
        if self.running:
            counts = buf.singles()
            print(counts)
            idx = 1
            for lbl in self.counts_labels:
                lbl.set_text('Ch %d: %d' % (idx, counts[idx-1]))
                idx += 1
            threading.Timer(1, self.update_counts, [widget, lbl]).start()

    def on_button_mousedown(self, widget, x, y, lbl):
        #self.on_button_pressed(widget, lbl)
        widget.style['background-color'] = 'red'
        widget.set_text('counting')

    def on_button_mouseup(self, widget, x, y, lbl):
        self.on_button_pressed(widget, lbl)

    def reset_button_pressed(self, widget, lbl):
        reset.reset()
        lbl.set_text('Finished reset')
        # widget.set_text('Hi!')



if __name__ == "__main__":
    # starts the webserver
    # optional parameters
    # start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
    start(MyApp, address='0.0.0.0', port=8081, debug=False, start_browser=False)

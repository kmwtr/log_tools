#! python3
import logging as log
import log_conf
import customtkinter
from PIL import ImageTk
import os

import ssf_utils

# ======== ========= ========= ========= ========= ========= ========= =========

# Font settings
bold = ('Segoe UI', 16, 'bold')
normal = ('Segoe UI', 14, 'normal')
small = ('Segoe UI', 12, 'normal')
monotype = ('Courier New', 14, 'normal')

class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, master, main_window_position, my_settings):
        super().__init__(master)
        log.debug('> class ' + type(self).__name__)

        self.master_obj = master
        
        # ウィンドウの設定
        self.title('Settings')
        self._set_windowicon()
        # ウィンドウサイズと位置の決定
        target_position = main_window_position
        target_position_str = '+' + str(target_position[0] + 120) + '+' + str(target_position[1] + 120)
        self.geometry(target_position_str)
        self.grid_columnconfigure([0,1], weight=1)
        
        #- --------- --------- --------- --------- --------- --------- ---------

        # Image save directory
        self.image_save_dir = EntoryFrame(self, label_text='Image save directory', default_text=my_settings['image_save_dir'])
        self.image_save_dir.grid(row=0, padx=0, pady=0, sticky='nsew', columnspan=2)

        # Exif 0x8298: Copyright (ASCII)
        self.exif_copyright = EntoryFrame(self, label_text='Exif 0x8298: Copyright (ASCII)', default_text=my_settings['exif_copyright'])
        self.exif_copyright.grid(row=1, padx=0, pady=0, sticky='nsew', columnspan=2)

        # Jpeg compression quarity (default: 90±2)
        self.jpeg_quarity = EntoryFrame(self, label_text='Jpeg compression quarity (default: 90±2)', default_text=my_settings['jpeg_quarity'])
        self.jpeg_quarity.grid(row=2, padx=0, pady=0, sticky='nsew', columnspan=2)

        # File name tag list
        tag_list_str = ', '.join(my_settings['tag'])
        self.tag_list = EntoryFrame(self, label_text='Tag list', default_text=tag_list_str)
        self.tag_list.grid(row=3, padx=0, pady=0, sticky='nsew', columnspan=2)

        # Use Mozjpeg (switch)
        # ...
        
        # Save button behavior (switch)
        # ...
        
        #- --------- --------- --------- --------- --------- --------- ---------

        # Save ボタン
        self.button_save = customtkinter.CTkButton(self, text='Save', command=self._save_config)
        self.button_save.configure(anchor='c', width=32)
        self.button_save.grid(row=6, column=0, padx=[16, 8], pady=16, sticky='nesw', columnspan=1)

        # Cancel ボタン
        self.button_cancel = customtkinter.CTkButton(self, text='Cancel', command=self._exit)
        self.button_cancel.configure(anchor='c', width=32)
        self.button_cancel.grid(row=6, column=1, padx=[8, 16], pady=16, sticky='nesw', columnspan=1)

    def _save_config(self):
        
        new_config_dict =  {
            'image_save_dir':   self.image_save_dir.text.get(), 
            'exif_copyright':   self.exif_copyright.text.get(), 
            'jpeg_quarity':     int(self.jpeg_quarity.text.get()), 
            'tag': []
            }
        
        s = self.tag_list.text.get()
        new_config_dict['tag'] = [x.strip() for x in s.split(',') if not x.strip() == '']
        
        print(new_config_dict)
        ssf_utils.save_ssf_config(new_config_dict, os.getcwd())
        
        self.master_obj.reload_config()

        self.destroy()
        self.update()

    def _exit(self):
        self.destroy()
        self.update()

    def _set_windowicon(self):
        iconpath = ImageTk.PhotoImage(file='assets\\ssf_favicon.png')
        self.wm_iconbitmap()
        # Toplevelのアイコンは200ミリ秒より後に指定する必要がある。
        # https://stackoverflow.com/questions/75825190/how-to-put-iconbitmap-on-a-customtkinter-toplevel
        self.after(220, lambda: self.iconphoto(False, iconpath))

# -------- --------- --------- --------- --------- --------- --------- ---------

class EntoryFrame(customtkinter.CTkFrame):
    def __init__(self, master, label_text, default_text):
        super().__init__(master)
        log.debug('> class ' + type(self).__name__)
        
        # 設定
        self.grid_columnconfigure(0, weight=1)

        # Label
        self.label = customtkinter.CTkLabel(self, text=label_text, anchor='w', font=normal, width=360)
        self.label.grid(row=0, padx=16, pady=[8, 0], sticky='nsew')

        # Entry
        self.text = customtkinter.StringVar()
        self.text.set(default_text)
        self.entry_default_save_dir = customtkinter.CTkEntry(self, textvariable=self.text)
        self.entry_default_save_dir.configure(font=monotype)
        self.entry_default_save_dir.grid(row=1, padx=[64, 16], pady=8, sticky='nsew')

# ======== ========= ========= ========= ========= ========= ========= =========

if __name__ == '__main__':
    print('Hello.')
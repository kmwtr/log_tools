#! python3
import logging as log
import log_conf
import sys
import customtkinter
from PIL import Image, ImageTk, ImageDraw
import os
import pprint

from img_edt import ImageEditor
import ssf_utils
import ssf_tlw


# GUI のカラーシーム
# ======== ========= ========= ========= ========= ========= ========= =========

col_lv0 = ['gray80', 'gray5']

drpd_fg_col = ['gray80', 'gray30']
subtext_col = ['gray30', 'gray60']

my_blue = ['#4799eb', '#1466b8']
#4799eb ... HSL: 210°, 80%, 60% 
#1466b8 ... HSL: 210°, 80%, 40%

my_blue_hv = ['#75b2f0', '#197fe6']
#75b2f0 ... HSL: 210°, 80%, 70% 
#197fe6 ... HSL: 210°, 80%, 50%

my_orange_hv = ['#f5993d', '#b86614']
#f5993d ... HSL: 30°, 90%, 60%
#b86614 ... HSL: 30°, 80%, 40%

unselected_col = ['gray60', 'gray30']
unselected_col_hov = ['gray70', 'gray40']

# Font settings
bold = ('Segoe UI', 16, 'bold')
normal = ('Segoe UI', 14, 'normal')
small = ('Segoe UI', 12, 'normal')
monotype = ('Courier New', 14, 'normal')


# GUIの構造
# ======== ========= ========= ========= ========= ========= ========= =========

frames_data = {
    'clip':     {
        'frame_id':     'clip',
        'title':        'Clip',
        'root_switch':  True,
        'button':       ['1:1', '4:3', '3:2', '16:9', '2:1'],
        'set_number':   1,
    },
    'resize':   {
        'frame_id':     'resize',
        'title':        'Resize',
        'root_switch':  True,
        'button':       ['2048', '1920', '1024', '640', '512'],
        'set_number':   3,
    },
    'format':   {
        'frame_id':     'format',
        'title':        'Format',
        'root_switch':  None,
        'button':       ['JPG', 'PNG'],
        'set_number':   0,
        'quarity':      90,
    }, 
    'naming':   {
        'frame_id':     'naming',
        'title':        'Naming',
        'root_switch':  None,
        'notes_text':   ['Date', 'Tag', 'ID'], 
        'date':         'YYMMDD', 
        'tag':          None, 
        'id':           ['', 'A', 'B', 'C', '1', '2', '3'],
    }, 
    'exif':     {
        'frame_id':     'exif',
        'title':        'Exif',
        'root_switch':  None,
        'user_comment': '',
        'copyright':    '',
    }, 
    'preview':    {
        'frame_id':     'preview',
        'title':        'Clipboard Image',
        'root_switch':  None,
    }, 
    'save':      {
        'frame_id':     'save',
        'title':        None,
        'root_switch':  None,
        'directory':    '',
    }
}

# ======== ========= ========= ========= ========= ========= ========= =========

class CTkApp(customtkinter.CTk):
    """GUIのルート"""
    def __init__(self):
        super().__init__(fg_color=col_lv0) # CTkの色はここで指定。
        log.debug('> class ' + type(self).__name__)

        # カレントディレクトリをこのファイルのディレクトリに移動
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        log.debug('getcwd: ' + os.getcwd())

        # CTk の各種設定
        #  --------- --------- --------- --------- --------- --------- ---------
        # カラーシーム
        customtkinter.set_default_color_theme('assets\\ssf_blue.json')
        #customtkinter.set_appearance_mode('light') # system (default), light, dark

        # ウィンドウの設定
        self.title('Screenshot Formatter | v0.2.0')
        self._set_windowicon()

        # ウィンドウサイズと位置の決定（CTkTopLevelでも利用）
        self.target_position = ssf_utils.calculate_window_position(720, 540)
        target_position_str = '+' + str(self.target_position[0]) + '+' + str(self.target_position[1])
        self.geometry('720x540' + target_position_str) 
        
        # ToplevelWindowを準備
        self.toplevel_window = None

        # 各フレームの準備
        #  --------- --------- --------- --------- --------- --------- ---------
        # 各設定の読み込み
        self.my_settings = ssf_utils.load_ssf_config(os.getcwd(), 'config.yaml')
        # 各設定を格納
        frames_data['format']['quarity'] =  self.my_settings['jpeg_quarity']
        frames_data['naming']['tag'] =      self.my_settings['tag']
        frames_data['exif']['copyright'] =  self.my_settings['exif_copyright']
        frames_data['save']['directory'] =  self.my_settings['image_save_dir']
        # 
        frames_data['naming']['date'] =  ssf_utils.today()

        # 各フレームのインスタンス化
        #  --------- --------- --------- --------- --------- --------- ---------
        # グリッドの設定
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure([1, 2], weight=1)
        
        # ClipboardImageEditor をクラス変数に格納
        CTkMultiFrame.myImgEditor = ImageEditor()

        # Clip
        clip_frame = CTkMultiFrame(self, data=frames_data['clip'])
        clip_frame.grid(row=0, column=0, padx=[8, 4], pady=[8, 0], sticky='nsew', columnspan=2)
        # Resize
        resize_frame = CTkMultiFrame(self, data=frames_data['resize'])
        resize_frame.grid(row=1, column=0, padx=[8, 4], pady=[8, 0], sticky='nsew', columnspan=2)
        # Format
        self.format_frame = CTkMultiFrame(self, data=frames_data['format'])
        self.format_frame.grid(row=2, column=0, padx=[8, 4], pady=[8, 0], sticky='nsew', columnspan=2)
        # Naming (Date, Tag, ID)
        self.naming_frame = CTkMultiFrame(self, data=frames_data['naming'])
        self.naming_frame.grid(row=3, column=0, padx=[8, 4], pady=[8, 0], sticky='nsew', columnspan=2)
        # Exif 
        self.exif_frame = CTkMultiFrame(self, data=frames_data['exif'])
        self.exif_frame.grid(row=4, column=0, padx=[8, 4], pady=[8, 0], sticky='nsew', columnspan=2)
        # Preview
        preview_frame = CTkMultiFrame(self, data=frames_data['preview'])
        preview_frame.grid(row=0, column=2, padx=[4, 8], pady=[8, 0], sticky='nsew', rowspan=5)
        # Setting
        self._create_setting_button()
        self.button_setting.grid(row=5, column=0, padx=[8, 0], pady=8, sticky="nesw", columnspan=1)
        # Save
        self.save_frame = CTkMultiFrame(self, data=frames_data['save'])
        self.save_frame.grid(row=5, column=1, padx=8, pady=8, sticky="nsew", columnspan=2)
        # このあたりの設計が微妙
        data = [clip_frame, resize_frame, self.format_frame, self.naming_frame, self.exif_frame]
        self.save_frame.set_nultiframe_instances(data)

    def _set_windowicon(self):
        # アイコン画像
        self.iconpath = ImageTk.PhotoImage(file='assets\\ssf_favicon.png')
        self.wm_iconbitmap()
        self.iconphoto(False, self.iconpath)

    def _create_setting_button(self):
        # 歯車画像
        img_gear = Image.open("assets\\gear.png")
        ctkimg_gear = customtkinter.CTkImage(img_gear)
        # ボタン
        self.button_setting = customtkinter.CTkButton(self, image=ctkimg_gear, text="", command=self._open_toplevel)
        self.button_setting.configure(anchor='c', width=32, corner_radius=8, fg_color=unselected_col, hover_color=my_orange_hv)

    def _open_toplevel(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            print('hello A')
            self.toplevel_window = ssf_tlw.ToplevelWindow(self, self.target_position, self.my_settings)  # create window if its None or destroyed
            self.toplevel_window.after(10, self.toplevel_window.lift) 
        else:
            print('hello B')
            self.toplevel_window.focus()  # if window exists focus it

    def reload_config(self):
        print('spark!')
        self.my_settings = ssf_utils.load_ssf_config(os.getcwd(), 'config.yaml')
        # どうなんやろ
        # 各設定を格納
        frames_data['format']['quarity'] =  self.my_settings['jpeg_quarity']
        frames_data['naming']['tag'] =      self.my_settings['tag']
        frames_data['exif']['copyright'] =  self.my_settings['exif_copyright']
        frames_data['save']['directory'] =  self.my_settings['image_save_dir']
        # format, naming, exif, save が更新対象。
        self.format_frame.update(frames_data['format'])
        self.naming_frame.update(frames_data['naming'])
        self.exif_frame.update(frames_data['exif'])
        self.save_frame.update(frames_data['save'])

# -------- --------- --------- --------- --------- --------- --------- ---------

class CTkMultiFrame(customtkinter.CTkFrame):
    """汎用CTkフレーム。クラス変数にImageEditorのインスタンスを1つ持つ。"""
    myImgEditor: ImageEditor # saveだけでなくpreviewでも利用したいので。
    config_pack = {
        'clip':         ['on', '1:1'], 
        'resize':       ['on', '256'], 
        'format':       ['static', 'GIF', 0],
        'naming':       ['static', 'YYMMDD', 'TAG', 'ID'], 
        'exif':         ['static', 'ユーザーコメント UTF-16', 'Copyright ASCII'], 
        'directory':    ['static', 'C:']
    }
    _need_preview = False
    _clip_root_switch = False

    def __init__(self, master, data: dict):
        super().__init__(master)
        log.debug('> class ' + type(self).__name__)

        self.frame_id = data['frame_id']

        # フレーム内レイアウト設定
        self.grid_columnconfigure([0, 1, 2], weight=1)

        # タイトル
        self.title_label = customtkinter.CTkLabel(self)
        if data['title'] is not None:
            self.title_label.configure(text=data['title'], font=normal, anchor='w')
            self.title_label.configure(width=360, height=12)
            self.title_label.grid(row=0, column=0, padx=8, pady=8, sticky='w', columnspan=3)

        # 機能は 動的(on/off) or 静的
        self.root_switch_state = customtkinter.StringVar(value='static')
        if data['root_switch'] is not None:
            # 動的機能
            self.root_switch_state.set(value='off')
            self.root_switch = customtkinter.CTkSwitch(
                self, text='', command=self._root_switch_callback, 
                variable=self.root_switch_state, onvalue='on', offvalue='off')
            self.root_switch.configure(width=32, switch_width=32, switch_height=16)
            self.root_switch.grid(row=0, column=2, padx=8, pady=8, sticky='e')
            # スイッチ有効化
            if data['root_switch'] is True:
                self.root_switch.select()

        # 各スタイルに分岐
        match data['frame_id']:
            case 'clip' | 'resize' | 'format':
                self._create_segmentedbutton(values=data['button'], set_number=data['set_number'])
                if 'quarity' in data:
                    # 微妙：GUIに無いものについてはここで入れてしまった。
                    CTkMultiFrame.config_pack['format'][2] = data['quarity']
            case 'naming':
                self._create_boxes(notes_text=data['notes_text'], date=data['date'], tag_list=data['tag'], id_list=data['id'])
            case 'exif':
                self._create_textbox()
                # 微妙：GUIに無いものについてはここで入れてしまった。
                CTkMultiFrame.config_pack['exif'][2] = data['copyright']
            case 'preview':
                self._create_imagepreview()
            case 'save':
                self._create_savebutton(target_directory=data['directory'])

    def set_nultiframe_instances(self, nultiframe_instances: list):
        """各インスタンスから情報を受け取る。Saveフレームのインスタンスからのみ使う。"""
        log.debug('> def ' + sys._getframe().f_code.co_name)
        self.nultiframe_instances = nultiframe_instances

    def update(self, data):
        """"format, naming, exif, save フレームの初期状態を更新する。"""
        log.debug('> def ' + sys._getframe().f_code.co_name)
        # 各スタイルに分岐
        match data['frame_id']:
            case 'format':
                CTkMultiFrame.config_pack['format'][2] = data['quarity']
            case 'naming':
                print('helloaaaa')
                self.combobox0.configure(values=data['tag'])
            case 'exif':
                CTkMultiFrame.config_pack['exif'][2] = data['copyright']
            case 'save':
                print('hello')
                self.save_dir.set(data['directory'])

    # ---- --------- --------- --------- --------- --------- --------- ---------
    
    def _update_config_pack(self):
        for mf_instance in self.nultiframe_instances:
            data = [mf_instance.root_switch_state.get()]
            match mf_instance.frame_id:
                case 'clip':
                    data.append(mf_instance.segemented_button_var.get())
                    CTkMultiFrame.config_pack['clip'] = data
                case 'resize':
                    data.append(mf_instance.segemented_button_var.get())
                    CTkMultiFrame.config_pack['resize'] = data
                case 'format':
                    data.append(mf_instance.segemented_button_var.get())
                    CTkMultiFrame.config_pack['format'][0:2] = data
                case 'naming':
                    data.extend([mf_instance.strvar_date.get(), mf_instance.strvar_tag.get(), mf_instance.strvar_id.get()])
                    CTkMultiFrame.config_pack['naming'] = data
                case 'exif':
                    text = mf_instance.textbox_exiftag.get("0.0", "end")
                    data.append(text.replace('\n', '')) # 改行コードが入っているので消す。（なんとなく）
                    CTkMultiFrame.config_pack['exif'][0:2] = data
                case _:
                    log.debug('xxx')

        data = [self.root_switch_state.get(), self.save_dir.get()]
        CTkMultiFrame.config_pack['directory'] = data

    # ---- --------- --------- --------- --------- --------- --------- ---------

    def _create_segmentedbutton(self, values: list, set_number: int):
        log.debug('> def ' + sys._getframe().f_code.co_name)
        # 現在押されているボタン
        self.segemented_button_var = customtkinter.StringVar()
        # セグメントボタン
        self.segmented_button = customtkinter.CTkSegmentedButton(
            self, values=values, variable=self.segemented_button_var, command=self._segmentedbutton_callback)
        self.segmented_button.configure(font=normal, border_width=2) # border_widthだけシームが効かない。なぜ
        # ボタンの状態
        self.segmented_button.set(values[set_number])
        if self.root_switch_state.get() == 'off':
            self._set_button_state_color(state=False)
        # 配置
        self.segmented_button.grid(row=1, column=0, padx=8, pady=[0, 12], sticky='ew', columnspan=3)
        
        # clipの情報のみpreviewのためにすぐ必要となる。
        if self.frame_id == 'clip':
            CTkMultiFrame.config_pack['clip'][1] = self.segemented_button_var.get()
            if self.root_switch_state.get() == 'on':
                CTkMultiFrame._clip_root_switch = True

    def _create_boxes(self, notes_text=[], date='', tag_list=[], id_list=[]):
        log.debug('> def ' + sys._getframe().f_code.co_name)
        
        self.sub_text_date = customtkinter.CTkLabel(self)
        self.sub_text_date.configure(text=notes_text[0], font=small, anchor='w', height=8, text_color=subtext_col)
        self.sub_text_date.grid(row=1, column=0, padx=[10, 2], pady=0, sticky='ew', columnspan=3)
        self.sub_text_tag = customtkinter.CTkLabel(self)
        self.sub_text_tag.configure(text=notes_text[1], font=small, anchor='w', height=8, text_color=subtext_col)
        self.sub_text_tag.grid(row=1, column=1, padx=[4, 2], pady=0, sticky='ew', columnspan=3)
        self.sub_text_id = customtkinter.CTkLabel(self)
        self.sub_text_id.configure(text=notes_text[2], font=small, anchor='w', height=8, text_color=subtext_col)
        self.sub_text_id.grid(row=1, column=2, padx=[4, 8], pady=0, sticky='ew', columnspan=3)

        # 日付
        self.strvar_date = customtkinter.StringVar()
        self.strvar_date.set(date)
        self.entry = customtkinter.CTkEntry(self, textvariable=self.strvar_date, placeholder_text='YY.MM.DD')
        self.entry.configure(font=monotype, width=80)
        self.entry.grid(row=2, column=0, padx=[8, 2], pady=[0, 12], sticky='ew')

        # Tag
        self.strvar_tag = customtkinter.StringVar()
        self.combobox0 = customtkinter.CTkComboBox(master=self, values=tag_list, variable=self.strvar_tag)
        self.combobox0.configure(font=monotype, dropdown_font=normal, dropdown_fg_color=drpd_fg_col, width=80)
        self.combobox0.grid(row=2, column=1, padx=[2, 2], pady=[0, 12], sticky='ew')

        # ID
        self.strvar_id = customtkinter.StringVar()
        combobox1 = customtkinter.CTkOptionMenu(master=self, values=id_list, variable=self.strvar_id)
        combobox1.configure(font=monotype, dropdown_font=normal, dropdown_fg_color=drpd_fg_col, width=80)
        combobox1.grid(row=2, column=2, padx=[2, 8], pady=[0, 12], sticky='ew')

    def _create_textbox(self):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        self.sub_text_exif = customtkinter.CTkLabel(self)
        self.sub_text_exif.configure(text='0x9286: UserComment (UTF-16)', font=small, anchor='w', height=8, text_color=subtext_col)
        self.sub_text_exif.grid(row=1, column=0, padx=[10, 2], pady=0, sticky='ew', columnspan=3)

        # UserComment
        self.textbox_exiftag = customtkinter.CTkTextbox(self)
        self.textbox_exiftag.configure(font=normal, height=32)
        self.textbox_exiftag.grid(row=2, column=0, padx=8, pady=[0, 12], sticky='new', columnspan=3, rowspan=2)

    def _create_imagepreview(self):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        self.title_label.configure(anchor='center', text_color=subtext_col)
        self.configure(fg_color=col_lv0)

        ctkimg_preview = None
        self.img_label = customtkinter.CTkLabel(self, image=ctkimg_preview, width=320, height=320)

        # ポーリング設定
        def schedule_next_execution():
            data = CTkMultiFrame.myImgEditor.get_preview_image()
            if (data[0] is True) or ((data[0] is not None) and (CTkMultiFrame._need_preview is True)):
                if CTkMultiFrame._clip_root_switch is True:
                    rect_settings = self._calculate_preview_rect(data[1].width, data[1].height)
                    draw = ImageDraw.Draw(data[1])
                    draw.rectangle(rect_settings[0], outline="red", width=(2 * rect_settings[1]))

                # Pillow Image を変換
                ctkimg_preview = customtkinter.CTkImage(data[1], size=[320 * data[2], 320 * data[3]])
                self.img_label.configure(image=ctkimg_preview)

                CTkMultiFrame._need_preview = False
            # 0.5秒後にschedule_next_executionを再度呼び出す
            self.after(500, schedule_next_execution)

        schedule_next_execution()
        
        self.img_label.configure(text='', anchor='center', fg_color=['gray60', 'gray15'])
        self.img_label.grid(row=1, column=0, padx=8, pady=32, sticky='ns', columnspan=3)

    def _calculate_preview_rect(self, width, height):
        # オリジナル画像の比率を取得
        orig_img_aspect_ratio = height / width
        # Clip設定を取得
        aspect_str = CTkMultiFrame.config_pack['clip'][1]
        x_y = aspect_str.split(':')
        aspect_ratio = int(x_y[1]) / int(x_y[0])
        # 描画すべき線の太さ係数
        line_width = 1
        # 描画領域の指定（切り出し時と似てるが違うので注意）
        if aspect_ratio >= orig_img_aspect_ratio:
            log.debug('Crop the height.')
            target_pix_x = height / aspect_ratio
            left = round((width - target_pix_x) / 2)
            right = target_pix_x + left
            coordinates = (left, 0, right, height)
            line_width = round(width / 320)
        elif orig_img_aspect_ratio > aspect_ratio:
            log.debug('Crop the width.')
            target_pix_y = width * aspect_ratio
            upper = round((height - target_pix_y) / 2)
            lower = target_pix_y + upper
            coordinates = (0, upper, width, lower)
            line_width = round(height / 320) 
        
        if line_width < 1:
            line_width = 1
        return [coordinates, line_width]

    def _create_savebutton(self, target_directory):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        self.label_subtext = customtkinter.CTkLabel(self, text="Save path")
        self.label_subtext.configure(font=small, anchor='w', height=8, text_color=subtext_col)
        self.label_subtext.grid(row=0, column=0, padx=[18,8], pady=[8, 4], sticky="sew", columnspan=2)

        # 保存ディレクトリ
        self.save_dir = customtkinter.StringVar()
        self.save_dir.set(target_directory)
        self.entry = customtkinter.CTkEntry(self, textvariable=self.save_dir, placeholder_text="save directory")
        self.entry.configure(font=monotype)
        self.entry.grid(row=1, column=0, padx=[16,8], pady=[0, 8], sticky="new", columnspan=2)
        
        # フロッピー画像
        png_floppy = Image.open("assets\\floppy.png")
        img_floppy = customtkinter.CTkImage(png_floppy)
        
        # 保存ボタン
        self.button = customtkinter.CTkButton(self, image=img_floppy, text="SAVE ", command=self._save_button_callback)
        self.button.configure(font=bold, width=64, corner_radius=4, height=48)
        self.button.grid(row=0, column=2, padx=[8,16], pady=16, sticky="nsew", rowspan=2)

    # ---- --------- --------- --------- --------- --------- --------- ---------

    def _root_switch_callback(self):
        log.debug('Root switch was pressed.         -> ' + self.root_switch_state.get())
        if self.root_switch.get() == 'off':
            self.segmented_button.configure(state='disabled', unselected_color=['gray80', 'gray20'], selected_color=['gray80', 'gray20'])
            if self.frame_id == 'clip':
                CTkMultiFrame._clip_root_switch = False
                CTkMultiFrame._need_preview = True
        elif self.root_switch.get() == 'on':
            self.segmented_button.configure(state='normal', unselected_color=unselected_col, selected_color=my_blue)
            if self.frame_id == 'clip':
                CTkMultiFrame._clip_root_switch = True
                CTkMultiFrame._need_preview = True

    def _segmentedbutton_callback(self, value):
        log.debug('Segmented button was pressed.    -> ' + value)
        # clipの情報のみpreviewに必要なので動的に代入する。
        if self.frame_id == 'clip':
            CTkMultiFrame.config_pack['clip'][1] = self.segemented_button_var.get()
            CTkMultiFrame._need_preview = True
        
    def _save_button_callback(self):
        log.debug('> def ' + sys._getframe().f_code.co_name)
        
        self._update_config_pack()
        pprint.pprint(CTkMultiFrame.config_pack, indent=4, sort_dicts=False)

        # 画像編集
        CTkMultiFrame.myImgEditor.configure(self.config_pack) #注：configureするとImageEditor内の_need_editフラグが立つ。
        CTkMultiFrame.myImgEditor.edit()
        CTkMultiFrame.myImgEditor.save()

# ======== ========= ========= ========= ========= ========= ========= =========

if __name__ == '__main__':
    myApp = CTkApp()
    myApp.mainloop()

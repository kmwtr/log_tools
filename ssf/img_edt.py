#! python3
import logging as log
import log_conf
import sys
import os
from PIL import Image, ImageGrab
import piexif
import subprocess


# ======== ========= ========= ========= ========= ========= ========= =========


class ClipboardManager():
    """クリップボード画像を取得・保持する。"""
    def __init__(self):
        log.debug('> class ' + type(self).__name__)
        # PIL のログレベルを変更（したい場合）
        self._set_pil_loglevel(log.INFO)
        # 画像オブジェクト
        self.imgobj = None
        # 更新チェック用バッファ
        self._imgobj_tmp = None
        
    def update(self) -> bool:
        """クリップボードを取得して、更新があったかどうかを返す。"""
        log.debug('> def ' + sys._getframe().f_code.co_name)
        # クリップボードの有無と更新の有無
        if self._get_clipboard_image() is True:
            if self.imgobj is None:
                self.imgobj = self._imgobj_tmp
                log.debug('This is 1st image.')
                return True
            else:
                if self.imgobj.size == self._imgobj_tmp.size:
                    log.debug('No image updates.')
                    return False
                else:
                    self.imgobj = self._imgobj_tmp
                    log.debug('This is new image.')
                    return True
        return None

    # ---- --------- --------- --------- --------- --------- --------- ---------

    def _get_clipboard_image(self) -> bool:
        # クリップボードを取得。
        self._imgobj_tmp = ImageGrab.grabclipboard()
        if isinstance(self._imgobj_tmp, Image.Image):
            log.debug('Clipboard image is exist.')
            return True
        else:
            log.debug('No clipboard image.')
            return False

    def _set_pil_loglevel(self, log_level):
        pil_logger = log.getLogger('PIL')
        pil_logger.setLevel(log_level)


# ======== ========= ========= ========= ========= ========= ========= =========


class ImageEditor():
    """画像を編集してファイルに出力する。"""
    def __init__(self):
        log.debug('> class ' + type(self).__name__)
        self._cbm = ClipboardManager()
        # こちらでも編集・保存用に画像オブジェクトを持つ。
        self._imgobj_edt = None
        # 各種計算・整形済みの編集・保存設定
        self._prepared_config = {
            'aspect_ratio':     None, 
            'pixel_size':       None, 
            'file_format':      None, 
            'jpeg_quarity':     None, 
            'name':             None, 
            'exif_bytes':       None,
            'save_directory':   None,
        }
        # 圧縮率でユーザーが指定した値は別途保持しておく
        self._jpeg_quarity_orig = 80
        # Mozjpeg の有無フラグ
        self._jpeg_engine = True
        # Windows の場合のテンポラリフォルダ（OS別処理は未実装…）
        self._usrtmp_dir = os.path.expanduser('~\AppData\Local\Temp')
        # Configureフラグ
        self._need_edit = False

    def configure(self, config_pack: dict, jpeg_engine=True):
        """画像の操作と出力に関する設定を受け取って整形・保持する。 clip, resize, format, naming, exif, directory"""
        log.debug('> def ' + sys._getframe().f_code.co_name)
        
        # 設定を一旦クリア
        for key in self._prepared_config:
            self._prepared_config[key] = None
        # 設定を整形
        self._set_aspect_ratio(config_pack.get('clip'))
        self._set_pixel_size(config_pack.get('resize'))
        self._set_format(config_pack.get('format'))
        self._set_file_name(config_pack.get('naming'))
        self._set_exif_bytes(config_pack.get('exif'))
        self._set_dir(config_pack.get('directory'))
        # フラグを立てる
        self._jpeg_engine = jpeg_engine
        self._need_edit = True
    
    def get_preview_image(self):
        """クリップボードを取得して、画像が有効であればimgobjのコピーとアスペクト比を返す。"""
        log.debug('> def ' + sys._getframe().f_code.co_name)
        flag = self._cbm.update()
        if flag is not None: # 1st or new image
            # e.g.) 4:3
            aspect_A = self._cbm.imgobj.width / self._cbm.imgobj.height # 1.333
            aspect_B = self._cbm.imgobj.height / self._cbm.imgobj.width # 0.75
            if aspect_A > aspect_B:
                x = 1
                y = aspect_B
            else:
                x = aspect_A
                y = 1
            return [flag, self._cbm.imgobj.copy(), x, y]
        return [None]

    def edit(self):
        """設定に従って画像を編集する。"""
        log.debug('> def ' + sys._getframe().f_code.co_name)
        # 取得／更新
        # ここもっと良い書き方ほしい
        clipboard_flag = self._cbm.update()
        if (clipboard_flag is None) or ((clipboard_flag is False) and (self._need_edit is False)):
            log.debug('No need for image editing. Cancels the process.')
            return
        # 画像オブジェクトを受けとる。
        self._imgobj_edt = self._cbm.imgobj
        if self._prepared_config['aspect_ratio'] != None:
            self._clip()
        if self._prepared_config['pixel_size'] != None:
            self._resize()
        if self._prepared_config['file_format'] == '.jpg':
            self._optimize_jpeg_quality()
        #リセット
        self._need_edit = False
        
    def save(self):
        """設定に従って画像を保存する。"""
        log.debug('> def ' + sys._getframe().f_code.co_name)
        # 画像の有無
        if self._imgobj_edt is None:
            log.debug('No image. Cancels the image save process.')
            return
        # ディレクトリの有無
        if os.path.isdir(self._prepared_config['save_directory']) is False:
            log.debug('No such directory. Cancels the image save process.')
            return
        # ファイルとして保存
        match self._prepared_config['file_format']:
            case '.png':
                tmp_name = self._prepared_config['name'] + self._prepared_config['file_format']
                tmp_path = os.path.join(self._prepared_config['save_directory'], tmp_name)
                self._imgobj_edt.save(tmp_path, 'PNG', optimize=True, compress_level=8, exif=self._prepared_config['exif_bytes'])
                # ↑pngの場合、ちゃんと'PNG'を指定する書き方でないと、exifが保存されない。
                log.debug('PNG file was saved.')
            case '.jpg':
                if self._jpeg_engine is True:
                    self._run_mozjpeg()
                    log.debug('JPEG file was saved with MozJpeg.')
                else:
                    tmp_name = self._prepared_config['name'] + self._prepared_config['file_format']
                    tmp_path = os.path.join(self._prepared_config['save_directory'], tmp_name)
                    self._imgobj_edt.convert('RGB').save(
                        tmp_path, 'JPEG', quality=self._prepared_config['jpeg_quarity'], optimize=True, exif=self._prepared_config['exif_bytes'])
                    # ↑PILドキュメントによるとqualityのデフォルト値は75(0~100)。95以上は非推奨とある。
                    log.debug('JPEG file was saved with PIL.')

    # ---- --------- --------- --------- --------- --------- --------- ---------

    def _set_aspect_ratio(self, config: list):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        if config[0] != 'off':
            x_y = config[1].split(':')
            aspect_ratio = int(x_y[1]) / int(x_y[0])
            self._prepared_config['aspect_ratio'] = aspect_ratio
            log.debug('Key ... aspect_ratio:    ' + str(self._prepared_config['aspect_ratio']))

    def _set_pixel_size(self, config: list):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        if config[0] != 'off':
            pixel_size = int(config[1])
            self._prepared_config['pixel_size'] = pixel_size
            log.debug('Key ... pixel_size:      ' + str(self._prepared_config['pixel_size']))

    def _set_format(self, config: list):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        file_format = '.' + config[1].lower()
        self._prepared_config['file_format'] = file_format
        log.debug('Key ... file_format:     ' + self._prepared_config['file_format'])
        
        if config[1] == 'JPG':
            self._jpeg_quarity_orig = config[2]
            self._prepared_config['jpeg_quarity'] = config[2]
            log.debug('Key ... jpeg_quarity:    ' + str(self._prepared_config['jpeg_quarity']))

    def _set_file_name(self, config: list):
        log.debug('> def ' + sys._getframe().f_code.co_name)
        
        # 不要な記号を削除
        config[1].translate(str.maketrans('', '', '.,_-/\\'))
        config[2].translate(str.maketrans('', '', '.,_-/\\'))
        # Date
        file_name = config[1]
        # Tag 
        if config[2] != '':
            file_name += ('_' + config[2])
            # ID
            if config[3] != '':
                file_name += ('_' + config[3])
        
        self._prepared_config['name'] = file_name
        log.debug('Key ... name:            ' + self._prepared_config['name'])

    def _set_exif_bytes(self, config: list):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        # Exifデータの雛形
        exif_dict = {
            '0th': {
                piexif.ImageIFD.Make:   b'Kwain',
                piexif.ImageIFD.Model:  b'ScreenshotFormatter',
            }
        }
        # UserComment 追加
        if config[1] != '':
            # exifのUserCommentは、先頭8文字で文字コードを示す。しかしunicodeの種類までは定められていない。
            text_encoding_scheme = b'\x55\x4e\x49\x43\x4f\x44\x45\x00' # <- 'UNICODE'
            # win11のプロパティで正常に表示するにはutf-16の必要があった。他でもutf-16で実装している系が多いようだ。
            user_comment_utf = text_encoding_scheme + config[1].encode('utf-16')
            # 'Exif' は雛形に含まれていないので丸ごと渡す
            exif_dict['Exif'] = {piexif.ExifIFD.UserComment: user_comment_utf}
        # Copyright 追加
        if config[2] != '':
            copyright_ascii = config[2].encode('ascii')
            # '0th' は雛形に存在するのでそれ以降を生成
            exif_dict['0th'][piexif.ImageIFD.Copyright] = copyright_ascii

        # Exifデータをバイナリに変換
        exif_bytes = piexif.dump(exif_dict)
        self._prepared_config['exif_bytes'] = exif_bytes
        log.debug('Key ... exif_bytes: (exif_dict->) ' + str(exif_dict))

    def _set_dir(self, config: list):
        log.debug('> def ' + sys._getframe().f_code.co_name)
        
        if config[1] != '':
            self._prepared_config['save_directory'] = config[1]
        
        log.debug('Key ... save_directory:  ' + str(self._prepared_config['save_directory']))

    # ---- --------- --------- --------- --------- --------- --------- ---------

    def _clip(self):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        orig_img_aspect_ratio = self._imgobj_edt.height / self._imgobj_edt.width

        log.debug('self._imgobj_edt.height: ' + str(self._imgobj_edt.width))
        log.debug('self._imgobj_edt.width:  ' + str(self._imgobj_edt.height))
        log.debug('orig_img_aspect_ratio:   ' + str(orig_img_aspect_ratio))
        
        # 切り出し領域の指定
        if self._prepared_config['aspect_ratio'] >= orig_img_aspect_ratio:
            log.debug('Crop the width.')
            target_pix_x = self._imgobj_edt.height / self._prepared_config['aspect_ratio']
            left = round((self._imgobj_edt.width - target_pix_x) / 2)
            right = self._imgobj_edt.width - left
            # (left, upper, right, lower) 二重括弧になるのを忘れずに。
            self._imgobj_edt = self._imgobj_edt.crop((left, 0, right, self._imgobj_edt.height))

        elif orig_img_aspect_ratio > self._prepared_config['aspect_ratio']:
            log.debug('Crop the height.')
            target_pix_y = self._imgobj_edt.width * self._prepared_config['aspect_ratio']
            upper = round((self._imgobj_edt.height - target_pix_y) / 2)
            lower = self._imgobj_edt.height - upper
            self._imgobj_edt = self._imgobj_edt.crop((0, upper, self._imgobj_edt.width, lower))
        
        log.debug('self._imgobj_edt.height: ' + str(self._imgobj_edt.width))
        log.debug('self._imgobj_edt.width:  ' + str(self._imgobj_edt.height))

    def _resize(self):
        log.debug('> def ' + sys._getframe().f_code.co_name)
        
        log.debug('self._imgobj_edt.height: ' + str(self._imgobj_edt.width))
        log.debug('self._imgobj_edt.width:  ' + str(self._imgobj_edt.height))
        
        self._imgobj_edt.thumbnail((self._prepared_config['pixel_size'], self._imgobj_edt.height), Image.LANCZOS)
        
        log.debug('self._imgobj_edt.height: ' + str(self._imgobj_edt.width))
        log.debug('self._imgobj_edt.width:  ' + str(self._imgobj_edt.height))

    def _optimize_jpeg_quality(self):
        log.debug('> def ' + sys._getframe().f_code.co_name)
        # ざっくり圧縮率決める
        # MAX: 2048^ == 4,194,304
        # MIN: 512^  ==   262,144
        # MIN以下とMAX以上の画像の圧縮率は一律で定数扱いとする

        min_reso = 262144  # 512^
        max_reso = 4194304
        reso_range = 3932160 # MAX - MIN
        target_reso = self._imgobj_edt.width * self._imgobj_edt.height

        # control range ... ±2
        if target_reso < min_reso:
            control_val = 2
        elif target_reso > max_reso:
            control_val = -2
        else:
            coefficient = (target_reso - min_reso) / reso_range
            log.debug('coefficient:             ' + str(coefficient))
            control_val = 2 - round(4 * coefficient)
        log.debug('control_val:             ' + str(control_val))
        
        self._prepared_config['jpeg_quarity'] = self._jpeg_quarity_orig + control_val
        log.debug('Key ... jpeg_quarity:    ' + str(self._prepared_config['jpeg_quarity']))

    def _run_mozjpeg(self):
        log.debug('> def ' + sys._getframe().f_code.co_name)

        # テンポラリフォルダに中間素材を出力
        mozjpg_input_path = os.path.join(self._usrtmp_dir, 'intermediate_img.png')
        self._imgobj_edt.save(mozjpg_input_path, 'PNG')

        # Mozjpegでjpegを作成。
        tmp_name = self._prepared_config['name'] + self._prepared_config['file_format']
        target_path = os.path.join(self._prepared_config['save_directory'], tmp_name)
        mozjpeg_command = ['cjpeg', '-quality', str(self._prepared_config['jpeg_quarity']), '-outfile', target_path, mozjpg_input_path]
        cp = subprocess.run(mozjpeg_command, encoding='utf-8', stdout=subprocess.PIPE)
        log.debug(cp)
        
        # Exifの追加
        piexif.insert(self._prepared_config['exif_bytes'], target_path)

        # 中間ファイル削除
        os.remove(mozjpg_input_path)


# ======== ========= ========= ========= ========= ========= ========= =========


if __name__ == '__main__':

    config_pack_dummy = {
        'clip':         ['on', '4:3'], 
        'resize':       ['on', '640'], 
        'format':       ['static', 'JPG', 90], 
        'naming':       ['static', '231231', 'TAG', 'A'], 
        'exif':         ['static', 'ユーザーコメント', 'Copyright'], 
        'directory':    ['static', 'D:\\WebSite\\'], 
        'dummy':        ['dummy text']
    }

    ie = ImageEditor()
    ie.configure(config_pack_dummy)
    ie.edit()
    ie.save()

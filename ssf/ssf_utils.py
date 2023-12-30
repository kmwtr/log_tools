#! python3
import logging as log
import log_conf
# today()
import sys
import datetime
# calculate_window_position()
import ctypes
# load_settings()
import os

from ruamel.yaml import YAML

# ======== ========= ========= ========= ========= ========= ========= =========

def today() -> str:
    """今日の日付をYYMMDD形式の文字列で返す。"""
    log.debug('> def ' + sys._getframe().f_code.co_name)
    t_delta = datetime.timedelta(hours=9)
    tz_jst = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(tz_jst)
    today_ymd = now.strftime('%y%m%d')
    log.debug('today_ymd: ' + today_ymd)
    return today_ymd

# ======== ========= ========= ========= ========= ========= ========= =========

def calculate_window_position(virtual_window_size_x, virtual_window_size_y) -> list:
    """CTkウィンドウがディスプレイの中心にくる座標を返す。（Windows依存）"""
    log.debug('> def ' + sys._getframe().f_code.co_name)
    
    # ディスプレイの物理解像度を取得
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    real_reso_x = user32.GetSystemMetrics(0)
    real_reso_y = user32.GetSystemMetrics(1)

    # ディスプレイのOSスケーリング値を取得
    scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

    # ウィンドウの物理ピクセル数を計算
    window_size_x = int(virtual_window_size_x * scaleFactor)
    window_size_y = int(virtual_window_size_y * scaleFactor)

    # ターゲット位置を計算
    target_position_x = int((real_reso_x - window_size_x) / 2)
    target_position_y = int((real_reso_y - window_size_y) / 2)

    log.debug('Physical display resolution: ' + str(real_reso_x) + ' x ' + str(real_reso_y) + ' px, ' + 
              'OS scaleFactor: x' + str(scaleFactor) + ', ' +
              'Physical Window resolution: ' + str(window_size_x) + ' x ' + str(window_size_y) + ' px, ' +
              'Physical target position: ' + str(target_position_x) + ' x ' + str(target_position_y) + ' px')
    
    # CTkのgeometry()は、ウィンドウは仮想ピクセル数を、マージンは実ピクセル数を要求しているっぽい。
    return target_position_x, target_position_y

# ======== ========= ========= ========= ========= ========= ========= =========

def load_ssf_config(ssf_root_dir: str, file_name='ssf_config.yaml') -> dict:
    """SSFの設定yamlを読み込む。"""
    log.debug('> def ' + sys._getframe().f_code.co_name)
    
    config_file_path = os.path.join(ssf_root_dir, 'assets', file_name)

    # ファイルのロード
    if os.path.isfile(config_file_path):
        yaml = YAML(typ='safe')
        with open(config_file_path, mode='r', encoding='utf-8') as stream:
            yaml_data = yaml.load(stream)
            settings = {
                'image_save_dir':   yaml_data['Image save dir'], 
                'exif_copyright':   yaml_data['Exif copyright'], 
                'jpeg_quarity':     yaml_data['Jpeg quarity'], 
                'tag':              yaml_data['Tag'], 
            }
    else:
        settings = {
            'image_save_dir':   'C:', 
            'exif_copyright':   '', 
            'jpeg_quarity':     90, 
            'tag':              [], 
        }
        log.debug('⚠️ No config file. Use default settings.')
        
    log.debug('settings: ' + str(settings))
    return settings

# -------- --------- --------- --------- --------- --------- --------- ---------

def save_ssf_config(config_dict: dict, ssf_root_dir: str, file_name='ssf_config.yaml'):
    """SSFの設定yamlを保存する。"""
    log.debug('> def ' + sys._getframe().f_code.co_name)

    config_file_path = os.path.join(ssf_root_dir, 'assets', file_name)

    settings = {
        'Image save dir':   config_dict['image_save_dir'], 
        'Exif copyright':   config_dict['exif_copyright'], 
        'Jpeg quarity':     config_dict['jpeg_quarity'], 
        'Tag':              config_dict['tag'], 
    }
    
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(sequence=4, offset=2)

    with open(config_file_path, mode='w', encoding='utf-8') as stream:
        yaml.dump(settings, stream)

# ======== ========= ========= ========= ========= ========= ========= =========

if __name__ == '__main__':
    today()
    calculate_window_position(640, 480)
    
    # カレントディレクトリをこのファイルのディレクトリに移動
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    data = load_ssf_config(os.getcwd(), 'ssf_config.yaml')
    save_ssf_config(data, os.getcwd())
    
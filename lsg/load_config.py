#! python3
import logging as log
import log_config
import sys
import os
from pathlib import Path
from pprint import pformat
import yaml

# ------------------------------------------------------------------------------=---------------------------------------

def load_lsg_config(file_name='lsg_config.yaml') -> dict:
    """LSGの設定yamlを読み込む。"""
    log.debug('> def ' + sys._getframe().f_code.co_name)

    #カレントディレクトリをこのファイルの階層に移動
    os.chdir(Path(__file__).resolve().parent)
    
    #現在のディレクトリ位置確認
    path = os.getcwd()
    log.debug('cwd_path:    ' + path)

    #設定を取得
    try:
        file = Path(file_name).read_text(encoding='utf-8')
    except OSError as e:
        log.debug(f'ERROR | {e}')
        return

    data = yaml.safe_load(file)

    year, quarter =     data['Year'], data['Quarter']
    base_dir =          data['Base Dir']
    img_dir, tmb_dir =  data['Image Dir Name'], data['Thumbnail Dir Name']
    html_dir =          data['HTML Dir Name']

    year =      str(year)
    base_dir =  Path(base_dir)
    img_dir =   base_dir / img_dir / year
    tmb_dir =   base_dir / tmb_dir / year
    html_dir =  base_dir / html_dir
    
    setting_dict = {
        'Year':         year,
        'Quarter':      quarter,
        'BaseDir':      base_dir,
        'ImageDir':     img_dir,
        'ThumbnailDir': tmb_dir,
        'HTMLDir':      html_dir
    }
    log.debug('setting_dict: \n' + pformat(setting_dict, indent=2))

    return setting_dict

# ------------------------------------------------------------------------------=---------------------------------------

if __name__ == '__main__':
    load_lsg_config()
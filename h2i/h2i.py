#! python3
import sys
import os
from pathlib import Path
import yaml
from operator import itemgetter
import hashlib
import datetime
from PIL import Image

# ------------------------------------------------------------------------------=-------------------

def main():
    tgt_path, prj_list, col_pal = itemgetter('TargetPath', 'ProjectList', 'ColorPalette')(load_config())
    today_string = today()

    print('Select the project Number.')
    for i, name in enumerate(prj_list):
        print(str(i) + ': ' + name + ' / ', end='')
    print()

    project_id = int(input())
    project_name = prj_list[project_id]
    print('Selected project: ' + str(project_id) + ': ' + project_name)
    
    project_name_hash = hashlib.sha1(project_name.encode('utf-8')).hexdigest()
    first_chunk = project_name_hash[0:8]
    print('first_chunk: ' + first_chunk)
    
    print('Input the commit hash')
    hex_string = input()
    if len(hex_string) != 40:
        print('Error: It is not sha1 hash')
        return

    long_string = first_chunk + hex_string
    print(long_string)

    rgb_pal = []
    for key in col_pal:
        rgb_pal.append(int(col_pal[key][0:2], 16))
        rgb_pal.append(int(col_pal[key][2:4], 16))
        rgb_pal.append(int(col_pal[key][4:6], 16))
    
    pixel_index_data = [int(idx, 16) for idx in long_string]
    print(pixel_index_data)

    # 8x6pxのインデックスカラーPNGを作成
    img = Image.new('P', (8, 6))
    img.putpalette(rgb_pal)
    img.putdata(pixel_index_data)
    img.save(tgt_path / (today_string + '_' + hex_string[0:8] + '.png'))
    print('Image saved at: ' + str(tgt_path / (today_string + '_' + first_chunk + '.png')))

# ------------------------------------------------------------------------------=-------------------

def load_config(file_name='config.yaml') -> dict:
    """設定yamlを読んで辞書に加工して返す。"""
    print('> def ' + sys._getframe().f_code.co_name)
    #カレントディレクトリをこのファイルの階層に移動
    os.chdir(Path(__file__).resolve().parent)
    #設定を取得
    config_string = Path('./config.yaml').read_text(encoding='utf-8')
    data = yaml.safe_load(config_string)
    #まとめる
    setting_dict = {
        'TargetPath':   Path(data['Target Path']), 
        'ProjectList':  data['Project List'],
        'ColorPalette': data['Color Palette']
    }
    #print(setting_dict)
    return setting_dict

def today() -> str:
    """今日の日付をYYMMDD形式の文字列で返す。"""
    print('> def ' + sys._getframe().f_code.co_name)
    t_delta = datetime.timedelta(hours=9)
    tz_jst = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(tz_jst)
    today_ymd = now.strftime('%y%m%d')
    print('today_ymd: ' + today_ymd)
    return today_ymd

# ------------------------------------------------------------------------------=-------------------

if __name__ == '__main__':
    main()
    input()
    
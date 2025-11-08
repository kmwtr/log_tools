#! python3
import logging as log
import log_config
import sys
from pprint import pformat
from pathlib import Path
from PIL import Image

# Pillow のログは消しとく
log.getLogger('PIL').setLevel(log.WARNING)

# ------------------------------------------------------------------------------=---------------------------------------

def is_large_file(item: Path, threshold_byte: int, threshold_resolution = 0) -> bool:
    #log.debug('> def ' + sys._getframe().f_code.co_name)

    if item.stat().st_size > threshold_byte:
        return True
    elif threshold_resolution != 0:
        # resolution_threshold が有効数字であれば解像度も確認する
        tmp_obj = Image.open(item)
        tmp_reso = tmp_obj.width * tmp_obj.height
        # ファイルサイズが小さくても解像度が大きければリストに入れる
        if tmp_reso > threshold_resolution:
            return True

    return False

def is_pixel_art(item: Path, threshold_resolution = 256) -> bool:
    #log.debug('> def ' + sys._getframe().f_code.co_name)
    
    tmp_obj = Image.open(item)
    tmp_reso = tmp_obj.width * tmp_obj.height

    # とりあえず単に小さいもの（デフォルト16x16==256以下）をTrueとする。
    if tmp_reso <= threshold_resolution:
        return True

    return False

# ------------------------------------------------------------------------------=---------------------------------------

def make_media_database(lsg_settings: dict) -> list:
    """メディアのデータベースを作成する"""
    log.debug('> def ' + sys._getframe().f_code.co_name)

    # 処理したいクオーターに含まれる月を割り出す
    base_num = int((lsg_settings['Quarter'] - 1) * 3)
    date_code = (
        lsg_settings['Year'] + str(base_num + 1).zfill(2), 
        lsg_settings['Year'] + str(base_num + 2).zfill(2), 
        lsg_settings['Year'] + str(base_num + 3).zfill(2)
        )

    #メディアファイルの各パラメータを辞書でデータベース化
    media_database = []
    large_file_counter = 0
    for item in lsg_settings['ImageDir'].iterdir():
        if item.is_file():
            #memo: item.name, item.stem, item.suffix で必要なものは取り出せる
            #命名ルール外の名前のものはとりあえず弾いとく。
            if ' ' in item.name:
                log.error('メディアファイル名にスペースが含まれています。ルール通り命名されたファイルしか処理できません。:\n' +
                          item.name)
                return
            # ターゲットのクオーター内のファイルのみ処理
            if item.stem.startswith(date_code):
                if item.suffix.lower() in {'.jpg', '.png'}:
                    file_type = 'img'
                    item_size = is_large_file(item, 128000)
                    pixel_art = is_pixel_art(item)
                elif item.suffix.lower() in {'.gif'}:
                    file_type = 'gif'
                    item_size = is_large_file(item, 512000, 43200) # 240 * 180 を超える場合
                    pixel_art = is_pixel_art(item)
                elif item.suffix.lower() in {'.mp4'}:
                    file_type = 'mp4'
                    item_size = is_large_file(item, 512000)
                    pixel_art = False
                # サムネイルの有無を確認
                tmb_exists = False
                expected_suffix = None
                if item_size == True:
                    # サムネイル数との突合せ用。とりあえず
                    large_file_counter += 1
                    # 予想されるサムネイル名を作成
                    if item.suffix.lower() == '.png':
                        expected_suffix = '.jpg'
                    elif  item.suffix.lower() == '.gif':
                        expected_suffix = '.mp4'
                    else:
                        expected_suffix = item.suffix
                    # 実際に確認する
                    expected_tmb_path = lsg_settings['ThumbnailDir'] / ('tmb_' + item.stem + expected_suffix)
                    if expected_tmb_path.exists():
                        tmb_exists = True                    
                media_database.append({'Path': item, 'Type': file_type, 'Large': item_size, 'Pixelated': pixel_art, 
                                    'Thumbnail': tmb_exists, 'TmbType': expected_suffix})
    log.debug('media_database:')
    for item in media_database:
        print(item['Path'])
        print('  Type: ' + item['Type'] + ', Large: ' + str(item['Large']) + ', Pixelated: ' + str(item['Pixelated']) + 
              ', Thumbnail: ' + str(item['Thumbnail']) + ', TmbType: ' + str(item['TmbType']))
    
    #サムネイルディレクトリが無い場合は作る
    lsg_settings['ThumbnailDir'].mkdir(parents=True, exist_ok=True)
    
    #現状サムネイルがいくつあるのか確認
    tmb_counter = 0
    for item in lsg_settings['ThumbnailDir'].iterdir():
        if item.is_file():
            if item.stem.startswith(date_code):
                tmb_counter += 1

    if tmb_counter != large_file_counter:
        log.warning('大きいメディアファイルとサムネイルの数が一致していません。')

    return media_database

# ------------------------------------------------------------------------------=---------------------------------------

if __name__ == '__main__':
    from load_config import load_lsg_config
    make_media_database(load_lsg_config())

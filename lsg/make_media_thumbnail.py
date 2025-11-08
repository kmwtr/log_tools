#! python3
import logging as log
import log_config as log_config
import sys
import os
import subprocess
from PIL import Image

# ------------------------------------------------------------------------------=---------------------------------------

def make_media_thumbnail(media_database, lsg_settings):
    """サムネイルメディアを作成する"""
    log.debug('> def ' + sys._getframe().f_code.co_name)
    
    for item in media_database:
        # サムネイルを作らないといけないもの
        if (item['Large'] == True) and (item['Thumbnail'] == False):
            print(item)
            if item['Type'] == 'img':
                make_image_thumbnail(item, lsg_settings)
            if (item['Type'] == 'video') or (item['Type'] == 'gif'):
                make_video_thumbnail(item, lsg_settings)
    return

# ------------------------------------------------------------------------------=---------------------------------------

def make_image_thumbnail(medida_param: dict, lsg_settings: dict):
    """サムネイル画像を作成する"""
    log.debug('> def ' + sys._getframe().f_code.co_name)
        
    # jpg, png を読む
    image_obj = Image.open(medida_param['Path'])
    image_obj = image_obj.convert('RGB') # 必要？
    
    # アスペクト比によってクリッピング処理を調整
    if image_obj.width > image_obj.height:
        aspect_ratio = round(image_obj.width / image_obj.height, 1)
        # 横長なら横長にクリッピングしてリサイズ
        if aspect_ratio < 1.333:
            # 4:3 よりも正方形に近い場合
            crop_pix_y = round((image_obj.height - ((image_obj.width * 3) / 4)) /2)
            image_obj = image_obj.crop((0, crop_pix_y, image_obj.width, image_obj.height - crop_pix_y))
        elif aspect_ratio <= 1.5:
            # 4:3 と 3:2(1.5:1) の間の場合
            crop_pix_x = round((image_obj.width - ((image_obj.height * 4) / 3)) / 2)
            image_obj = image_obj.crop((crop_pix_x, 0, image_obj.width - crop_pix_x, image_obj.height))
        # thumbnail関数はアスペクト比を維持して拡大縮小してくれる
        image_obj.thumbnail((640, 480), Image.LANCZOS)
    else:
        # 縦長なら正方形にクリッピングしてリサイズ
        image_obj = image_obj.crop((0, (image_obj.height - image_obj.width)/2, 
                                    image_obj.width, image_obj.width + (image_obj.height - image_obj.width)/2))
        image_obj.thumbnail((480, 480), Image.LANCZOS)
    
    # 一旦Pillowでpngとして出力
    intermediate_png_path = lsg_settings['ThumbnailDir'] / ('tmb_' + medida_param['Path'].stem + '.png')
    image_obj.save(intermediate_png_path)
    #image_obj.save(dirs_list['tmb_img_dir'] + 'tmb_' + tmp_name + '.jpg', quality=80) # jpgの場合
    log.debug('Saved intermediate PNG: ' + str(intermediate_png_path))
    
    # mozjpg を呼び出してjpgに圧縮する
    log.debug('| -> run MozJPEG')

    # 圧縮、中間ファイルとして出力
    intermediate_jpg_path = lsg_settings['ThumbnailDir'] / 'intermediate_img.jpg'
    cp = subprocess.run(['cjpeg', '-quality', '80', '-outfile', intermediate_jpg_path, intermediate_png_path], 
                        encoding='utf-8', stdout=subprocess.PIPE)
    log.debug(cp)
    log.debug('Saved intermediate JPG: ' + str(intermediate_jpg_path))

    # Exif 等メタデータを削除、最終ファイル出力
    output_path = lsg_settings['ThumbnailDir'] / ('tmb_' + medida_param['Path'].stem + '.jpg')
    cp = subprocess.run(['jpegtran', '-copy', 'none', '-optimize', '-outfile', output_path, intermediate_jpg_path], 
                         encoding='utf-8', stdout=subprocess.PIPE)
    log.debug(cp)
    log.debug('Saved Thumbnail: ' + str(output_path))

    # 中間ファイル削除
    os.remove(intermediate_png_path)
    os.remove(intermediate_jpg_path)

def make_video_thumbnail(medida_param: dict, lsg_settings: dict):
    """サムネイル動画を作成する"""
    log.debug('> def ' + sys._getframe().f_code.co_name)
    
    source_path = medida_param['Path']
    target_path = lsg_settings['ThumbnailDir'] / ('tmb_' + medida_param['Path'].stem + '.mp4')

    # ffmpeg
    option = [
        'ffmpeg', 
        '-i', source_path, 
        '-vf', 'scale=480:-1', 
        '-r', '12', 
        '-crf', '26', 
        '-maxrate', '400K', 
        '-bufsize', '800K', 
        '-pix_fmt', 'yuv420p', 
        '-vcodec', 'libx264', 
        target_path
        ]
    
    cp = subprocess.run(option, shell=True, encoding='utf-8', stdout=subprocess.PIPE) # shell=True 重要!
    log.debug(cp)

# ------------------------------------------------------------------------------=---------------------------------------

if __name__ == '__main__':
    from load_config import load_lsg_config
    from make_media_database import make_media_database

    lsg_settings = load_lsg_config()
    media_database = make_media_database(lsg_settings)
    make_media_thumbnail(media_database, lsg_settings)
    #os.system('PAUSE')
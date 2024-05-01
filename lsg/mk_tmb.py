#! python3
import logging as log
import log_conf
import sys
import os
import subprocess
from PIL import Image

def make_image_thumbnail(image_lists: dict, dirs_list: dict):
    """サムネイル画像を作成する"""
    log.debug('> def ' + sys._getframe().f_code.co_name)

    # jpg, png をサムネイル処理する
    candidate_img_list = image_lists['candidate_img_list']

    for i in range(len(candidate_img_list)):
        # 候補リストに基づいて jpg, png を読む
        image_obj = Image.open(dirs_list['src_img_dir'] + candidate_img_list[i])
        image_obj = image_obj.convert('RGB') # 必要???

        # アスペクト比によって別処理
        pixel_width = image_obj.width
        pixel_height = image_obj.height
        aspect_ratio = round(pixel_width / pixel_height, 1)

        if pixel_width > pixel_height:
            # 横長
            if aspect_ratio < 1.3:
                # 4:3 よりも正方形に近い場合
                crop_pix_y = round((pixel_height - ((pixel_width * 3) / 4)) /2)
                image_obj = image_obj.crop((0, crop_pix_y, pixel_width, pixel_height - crop_pix_y))
            elif aspect_ratio <= 1.5:
                # 4:3 と 3:2(1.5:1) の間の場合
                crop_pix_x = round((pixel_width - ((pixel_height * 4) / 3)) / 2)
                image_obj = image_obj.crop((crop_pix_x, 0, pixel_width - crop_pix_x, pixel_height))
            
            # 横長なら横長としてリサイズ
            image_obj.thumbnail((640, 480), Image.LANCZOS)
        else:
            # 縦長なら正方形にクリッピングしてリサイズ
            image_obj = image_obj.crop((0, (pixel_height - pixel_width)/2, pixel_width, pixel_width + (pixel_height - pixel_width)/2))
            image_obj.thumbnail((480, 480), Image.LANCZOS)
    
        # 一旦pngとして出力
        tmp_name = candidate_img_list[i].split('.')[0]
        tmp_path = dirs_list['tmb_img_dir'] + 'tmb_' + tmp_name + '.png'
        image_obj.save(tmp_path)
        #image_obj.save(dirs_list['tmb_img_dir'] + 'tmb_' + tmp_name + '.jpg', quality=80) # jpgの場合

        log.debug('saved_tmp-tmb: ' + 'tmb_' + tmp_name + '.png')
        
        # mozjpg を呼び出してjpgに圧縮する
        log.debug('| -> run MozJPEG')
        
        output_path = dirs_list['tmb_img_dir'] + 'tmb_' + tmp_name + '.jpg'

        # 圧縮、中間ファイルとして出力
        cp = subprocess.run(['cjpeg', '-quality', '80', '-outfile', dirs_list['tmb_img_dir'] + 'intermediate_img.jpg', tmp_path], encoding='utf-8', stdout=subprocess.PIPE)
        log.debug(cp)

        # Exif 等メタデータを削除、最終ファイル出力
        cp = subprocess.run(['jpegtran', '-copy', 'none', '-optimize', '-outfile', output_path, dirs_list['tmb_img_dir'] + 'intermediate_img.jpg'], encoding='utf-8', stdout=subprocess.PIPE)
        log.debug(cp)

        log.debug('saved_tmb: ' + 'tmb_' + tmp_name + '.jpg')

        # 中間ファイル削除
        os.remove(tmp_path)
        os.remove(dirs_list['tmb_img_dir'] + 'intermediate_img.jpg')


def make_video_thumbnail(key_name: str, image_lists: dict, dirs_list: dict):
    """サムネイル動画を作成する"""
    log.debug('> def ' + sys._getframe().f_code.co_name)
    
    candidate_file_list = image_lists[key_name]

    for i in range(len(candidate_file_list)):
        
        source_path = dirs_list['src_img_dir'] + candidate_file_list[i]
        target_path = dirs_list['tmb_img_dir'] + 'tmb_' + candidate_file_list[i]
        target_path = target_path.replace('.gif', '.mp4')

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


# EOL
def make_gif_thumbnail(image_lists: dict, dirs_list: dict):
    log.debug('-> make_gif_thumbnail()')

    # gif をサムネイル処理する
    candidate_gif_list = image_lists['candidate_gif_list']

    for i in range(len(candidate_gif_list)):
        # Gifsicle を呼び出して圧縮する（PIL でやるのは諦めた。）
        log.debug('| -> run Gifsicle')
        
        output_path = dirs_list['tmb_img_dir'] + 'tmb_' + candidate_gif_list[i]
        log.debug(dirs_list['src_img_dir'] + candidate_gif_list[i])

        image_obj = Image.open(dirs_list['src_img_dir'] + candidate_gif_list[i])
        
        # アスペクト比を維持
        size_x = image_obj.width
        size_y = image_obj.height
        resize_height = 240 * size_y // size_x

        # 圧縮、中間ファイルとして出力
        cp = subprocess.run(['gifsicle','--resize', '240x' + str(resize_height), '--optimize=3', '--colors', '256', '--lossy=40', dirs_list['src_img_dir'] + candidate_gif_list[i], '>', output_path], shell=True, encoding='utf-8', stdout=subprocess.PIPE) # shell=True 重要!
        log.debug(cp)


# -------------------------------------------------

if __name__ == '__main__':
    from load_conf import load_settings
    from mk_mflist import image_list

    dirs_list = load_settings()
    image_lists_dict = image_list(dirs_list)
    #make_gif_thumbnail(image_lists_dict, dirs_list)
    make_image_thumbnail(image_lists_dict, dirs_list)
    make_video_thumbnail('candidate_gif_list', image_lists_dict, dirs_list)
    make_video_thumbnail('candidate_mp4_list', image_lists_dict, dirs_list)
    #os.system('PAUSE')
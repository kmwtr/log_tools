#! python3
import os
import copy
import re
import logging as log
from jinja2 import Template, Environment, FileSystemLoader

import log_conf

from load_conf import load_lsg_config
from mk_mflist import make_mediafile_list
from mk_tmb import make_image_thumbnail, make_video_thumbnail

# -------------------------------------------------

def log_assets_processor():
    log.debug('-> log_assets_processor()')

    # 設定のロード
    settings = load_lsg_config()

    # ファイルリストの作成
    mediafile_lists_dict = make_mediafile_list(settings)

    # サムネイル作成
    make_image_thumbnail(mediafile_lists_dict, settings)
    make_video_thumbnail('candidate_gif_list', mediafile_lists_dict, settings)
    make_video_thumbnail('candidate_mp4_list', mediafile_lists_dict, settings)
    
    # 以下うーんって感じだけどとりあえずこれで

    # サムネイルリストを再取得（make_image_thumbnail() で増えている可能性があるため）
    mediafile_lists_dict['thumbnail_media_list'] = os.listdir(settings['tmb_img_dir'])

    # ファイルリストの順番を降順にする
    mediafile_lists_dict['source_media_list'].sort(reverse=True)
    mediafile_lists_dict['thumbnail_media_list'].sort(reverse=True)

    # このクオーターに属する月を文字列として成形する
    base_num = int((settings['quarter'] - 1) * 3)
    date_code = (
        str(settings['year']) + str(base_num + 1).zfill(2), 
        str(settings['year']) + str(base_num + 2).zfill(2), 
        str(settings['year']) + str(base_num + 3).zfill(2)
        )
    tmb_date_code = (
        'tmb_' + str(settings['year']) + str(base_num + 1).zfill(2), 
        'tmb_' + str(settings['year']) + str(base_num + 2).zfill(2), 
        'tmb_' + str(settings['year']) + str(base_num + 3).zfill(2)
        )

    log.debug('date_code: ' + str(date_code))
    
    # 処理したいクオーター内の名前リストを作成
    tmb_database = []
    file_database = []
    
    # サムネイルリストを走査
    for file_name in mediafile_lists_dict['thumbnail_media_list']:
        # 処理したいクオーター内のサムネイルファイル名を処理
        if file_name.startswith(tmb_date_code):
            # ファイル名と拡張子を分離
            data_name = os.path.splitext(file_name)
            # 
            tmb_database.append(data_name)

    # ファイルリストを走査
    for file_name in mediafile_lists_dict['source_media_list']:
        # 処理したいクオーター内のファイル名を処理
        if file_name.startswith(date_code):
            # ファイル名と拡張子を分離
            data_name = os.path.splitext(file_name)
            # リストを予約
            tmp_data = [data_name, data_name, False] # [0]ファイル、[1]サムネイル、[2]フラグ
            for tmb_name in tmb_database:
                if tmb_name[0].lstrip('tmb_') == data_name[0]:
                    tmp_data[1] = tmb_name
                    tmp_data[2] = True
            # 
            file_database.append(tmp_data)

    log.debug('file_database: \n' + str(file_database))

    # タグを成形 
    template_str_image   = '<img src="{{ thumbnail_path }}">'
    template_str_video   = '<video src="{{ thumbnail_path }}" loop muted autoplay playsinline></video>'
    template_obj_image = Template(template_str_image)
    template_obj_video = Template(template_str_video)

    item_dict = {
        'title': 'log | ' + str(settings['year']) + ' q' + str(settings['quarter']),
        'h2' : '20' + str(settings['year']) + ' q' + str(settings['quarter']),
        'items': [
            {'name': '220515_FXXX', 'path': '../img/22/220515_FXXX.png', 'thumbnail_path' : '../img/22/220515_FXXX.png'},
            {'name': '220515_FYYY', 'path': '../img/22/220515_FYYY.png', 'thumbnail_path' : '../img/22/220515_FYYY.png'}
        ]
    }

    tmp_list = []

    for data in file_database:
        href_top = '../img/' + str(settings['year']) +'/'
        if data[2] == True:
            # サムネイル有り
            href_top = '../tmb/' + str(settings['year']) +'/'

        tag_str = ''
        if data[1][1] == '.mp4':
            tag_str = template_obj_video.render(thumbnail_path = href_top + data[1][0] + data[1][1])
        else:
            tag_str = template_obj_image.render(thumbnail_path = href_top + data[1][0] + data[1][1])

        tmp_list.append({'name': data[0][0], 'href': '../img/' + str(settings['year']) +'/' + data[0][0] + data[0][1], 'tag' : tag_str})

    item_dict['items'] = tmp_list

    log.debug('item_dict["items"]:')
    log.debug(item_dict['items'])

    # テンプレートの読み込み
    env = Environment(loader=FileSystemLoader(settings['html_template_dir'], encoding='utf8'))
    tmpl = env.get_template('log_quarter_page_template.html')
    ren_s = tmpl.render(item_dict) # このタイミングで置き換えが行われる。
    
    print(ren_s)

    # htmlファイルの読み込み
    target_file = open(settings['html_path'], 'w', encoding='utf-8')
    target_file.write(ren_s)
    target_file.close()

    log.debug('FINISH')

if __name__ == '__main__':
    log_assets_processor()

#! python3
import sys
import os
import logging as log
from jinja2 import Template, Environment, FileSystemLoader

import log_config as log_config

from load_config import load_lsg_config
from make_media_database import make_media_database
from make_media_thumbnail import make_media_thumbnail
import operator

# ------------------------------------------------------------------------------=---------------------------------------

def log_site_generator():
    log.debug('> def ' + sys._getframe().f_code.co_name)

    # 設定のロード
    lsg_settings = load_lsg_config()

    # メディアデータベースの作成
    media_database = make_media_database(lsg_settings)

    # サムネイルの作成
    make_media_thumbnail(media_database, lsg_settings)
    
    # データベースの再構築
    media_database = make_media_database(lsg_settings)

    # データベースを降順にする
    media_database = sorted(media_database, key=operator.itemgetter('Path'), reverse=True)

    # タグを成形
    content_source = {
        'title':    'log | ' + lsg_settings['Year'] + ' q' + str(lsg_settings['Quarter']),
        'h2' :      '20' + lsg_settings['Year'],
        'h3' :      'q' + str(lsg_settings['Quarter'])
    }
    template_str_image = '<img src="{{ thumbnail_path }}" class="{{ image_attribute }}">'
    template_str_video = '<video src="{{ thumbnail_path }}" loop muted autoplay playsinline></video>'
    template_obj_image = Template(template_str_image)
    template_obj_video = Template(template_str_video)

    # content_sourceのitemsを作る
    tmp_list = []
    for item in media_database:
        tag_str = ''
        tmb_path = item['Path']
        img_attribute = ''
        element_type = item['Type']
        if item['Thumbnail'] == True:
            element_type = item['TmbType']
            tmb_path = lsg_settings['ThumbnailDir'] / ('tmb_' + item['Path'].stem + element_type)
        if item['Pixelated'] == True:
            img_attribute = 'pixelated'
        # posix形式の相対パスにしとく
        tmb_path = '../' + tmb_path.relative_to(lsg_settings['BaseDir']).as_posix()
        # タグ全体を作成
        if element_type == '.mp4':
            tag_str = template_obj_video.render(thumbnail_path = tmb_path)
        else:
            tag_str = template_obj_image.render(thumbnail_path = tmb_path, image_attribute = img_attribute)
        # posix形式の相対パスにしとく
        href_str = '../' + item['Path'].relative_to(lsg_settings['BaseDir']).as_posix()
        # タグ追加
        tmp_list.append({'href': href_str, 'elements_tag' : tag_str, 'caption': item['Path'].stem})
    # items追加
    content_source['items'] = tmp_list

    # テンプレートの読み込み
    env = Environment(loader=FileSystemLoader(lsg_settings['HTMLDir'], encoding='utf8'))
    tmpl = env.get_template('log_quarter_page_template.html')
    ren_s = tmpl.render(content_source) # このタイミングで置き換えが行われる。
    
    log.debug('generated html string')
    #print(ren_s)

    # htmlファイルの読み込み
    target_file = open(lsg_settings['HTMLDir'] / (lsg_settings['Year'] + 'q' + str(lsg_settings['Quarter']) + '.html'),
                       'w', encoding='utf-8')
    print(lsg_settings['HTMLDir'] / (lsg_settings['Year'] + 'q' + str(lsg_settings['Quarter'])))
    target_file.write(ren_s)
    target_file.close()

    log.debug('FINISH')

if __name__ == '__main__':
    log_site_generator()

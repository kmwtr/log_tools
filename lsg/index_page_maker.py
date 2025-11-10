#! python3
import sys
import os
import logging as log
import log_config as log_config
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader
import yaml
from pprint import pprint

# ------------------------------------------------------------------------------=---------------------------------------

def load_index_page_yaml(lsg_settings, file_name='index.yaml') -> dict:
    """index.yamlを読み込む。"""
    log.debug('> def ' + sys._getframe().f_code.co_name)
    
    yaml_path = lsg_settings['BaseDir'] / file_name
    #設定を取得
    try:
        file = Path(yaml_path).read_text(encoding='utf-8')
    except OSError as e:
        log.debug(f'ERROR | {e}')
        return
    data = yaml.safe_load(file)
    #pprint(data)

    return data

def generate_index_page(lsg_settings, index_page_selection):
    log.debug('> def ' + sys._getframe().f_code.co_name)

    no_img_element_tag = '<figure><div class="no_img"><img src="./asset/no_img.png"></div><figcaption>no media</figcaption></figure>'
    
    template_str_image = '<img src="{{ thumbnail_path }}" class="{{ image_attribute }}">'
    template_str_video = '<video src="{{ thumbnail_path }}" loop muted autoplay playsinline></video>'
    template_obj_image = Template(template_str_image)
    template_obj_video = Template(template_str_video)

    template_str = '<figure><a href="{{ href }}">{{ elements_tag }}</a><figcaption>{{ name }}<br>{{ caption }}</figcaption></figure>'
    template_obj = Template(template_str)
    
    # タグを成形
    content_source = []
    for key_year in index_page_selection:
        #print(key_year)
        counter = 0
        for key_quarter in index_page_selection[key_year]:
            #print(key_quarter)
            q_page_href = lsg_settings['HTMLDir'] / (str(key_year - 2000) + key_quarter.lower() + '.html')
            tmp = {'h2': '', 'h2_alt': key_year, 'h3': key_quarter.lower(), 
                'q_page_href': './' + q_page_href.relative_to(lsg_settings['BaseDir']).as_posix(), 'content': []}
            if counter == 0:
                tmp['h2'] = key_year
            for i, q_content in enumerate(index_page_selection[key_year][key_quarter]):
                #print(q_content)
                index_str = 'test_href_path'
                #elements_tag = template_obj_image.render(thumbnail_path = 'testpath', image_attribute = 'testattr')
                elements_tag = '<img>'
                tmp['content'].append(template_obj.render(href = index_str, elements_tag = elements_tag, name = q_content['file_name'], caption = q_content['caption']))
            for i in range(4 - len(index_page_selection[key_year][key_quarter])):
                # 埋める
                index_str = str(i)
                tmp['content'].append(no_img_element_tag)
            content_source.append(tmp)
            counter += 1
    
    pprint(content_source)
    test_dict = {'quarter_group': content_source}

    # テンプレートの読み込み
    env = Environment(loader=FileSystemLoader(lsg_settings['BaseDir'], encoding='utf8'))
    tmpl = env.get_template('index_page_template.html')
    ren_s = tmpl.render(test_dict) # このタイミングで置き換えが行われる。
    
    log.debug('html generated')
    #print(ren_s)
    
    # htmlファイルの読み込み
    target_file = open(lsg_settings['BaseDir'] / 'index_test.html', 'w', encoding='utf-8')
    target_file.write(ren_s)
    target_file.close()

# ------------------------------------------------------------------------------=---------------------------------------

if __name__ == '__main__':
    from load_config import load_lsg_config
    from make_media_database import make_media_database
    # 設定のロード
    lsg_settings = load_lsg_config()
    #media_database = make_media_database(lsg_settings) # 全期間から抽出する必要があるので、これは使えない…。
    index_page_selection = load_index_page_yaml(lsg_settings)
    generate_index_page(lsg_settings, index_page_selection)

#! python3
import logging as log
import log_conf
import sys
import os
import glob
import yaml

# -----------------------------------------------------------------------------

def load_lsg_config(file_name='lsg_config.yaml') -> dict:
    """LSGの設定yamlを読み込む。"""
    log.debug('> def ' + sys._getframe().f_code.co_name)

    # 現在のディレクトリ位置
    path = os.getcwd()
    log.debug('cwd_path:    ' + path)
    
    # 設定ファイルの取得（1階層下まで許容）
    yaml_name = file_name

    if not glob.glob(yaml_name):
        yaml_list = glob.glob(path + '/**/' + yaml_name)

        if not yaml_list:
            log.debug('ERROR | No Setting File')
            return
        
        if not len(yaml_list) == 1:
            log.debug('ERROR | There are many Files')
            return
        
        yaml_name = str(yaml_list[0])

    log.debug('yaml_dir:    ' + yaml_name)

    # ファイルのロード
    file = open(yaml_name, "r", encoding='utf-8')
    data = yaml.safe_load(file)

    year =              data["Year"]
    quarter =           data["Quarter"]

    base_dir =          str(data["Base DIR"])
    src_img_dir =       base_dir + str(data["Source Image DIR"]) + '/' + str(year) + '/'
    tmb_img_dir =       base_dir + str(data["Thumbnail Image DIR"]) + '/' + str(year) + '/'
    html_template_dir = base_dir + str(data["Target HTML DIR"]) + '/'
    html_path =         base_dir + str(data["Target HTML DIR"]) + '/' + str(year) + 'q'+ str(quarter) + '.html'

    setting_dict = {
        'year':             year, 
        'quarter':          quarter, 
        'base_dir':         base_dir, 
        'src_img_dir':      src_img_dir, 
        'tmb_img_dir':      tmb_img_dir, 
        'html_template_dir':html_template_dir,
        'html_path':        html_path,
        }
    
    log.debug('setting_dict: \n' + str(setting_dict))

    return setting_dict

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    load_lsg_config()
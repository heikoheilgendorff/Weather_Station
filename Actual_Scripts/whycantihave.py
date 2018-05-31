'''
This script will identify your operating system and fix your path notation accordingly

'''


def check_windows(path,plot_path):
    p = platform.system()
    iswin = 0
    if p == 'Windows':
        path = string.replace(path,'/','\\')
        plot_path = string.replace(plot_path,'/','\\')
        iswin = 1
    return path, plot_path, iswin
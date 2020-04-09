import os
import glob
import argparse

#from matplotlib import rcParams
#rcParams['font.family'] = 'sans-serif'
#rcParams['font.sans-serif'] = ['Tahoma']
#rcParams['font.family'] = 'serif'
#rcParams['font.serif'] = 'Times New Roman'

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, PercentFormatter


#def _fig(w=5, h=3.5):
#    return plt.figure(figsize=(w, h)).add_subplot(111)

def _fig(w=8./1.5, h=5/1.5):
    return plt.figure(figsize=(w, h)).add_subplot(111)

axes_map = {}

def mkAXS(key=0, **kwargs):
    ax = _fig(**kwargs)
    axes_map[key] = ax
    return ax


def calc_pdf(lst):
    pdf = {}
    for k in lst:
        pdf[k] = 1. + pdf.get(k, 0)  # 如果计算key的个数
    total = len(lst)
    for k in pdf:
        pdf[k] /= total  # 计算概率
    return pdf


def calc_cdf(lst, m=12):
    pdf = calc_pdf(lst)
    cdf = {}
    t_cp = 0
    xx = []
    yy = []
    last_cp = -1
    for k in sorted(pdf):
        t_cp += pdf[k]
        if t_cp > last_cp:
            last_cp = t_cp
            cdf[k] = t_cp
            xx.append(k)
            yy.append(t_cp)

    return xx, yy, cdf


def show():
    #plt.show()
    #return
    for name, ax in axes_map.items():
        #ax.legend()
        plt.sca(ax)
        ticklines = ax.xaxis.get_ticklines()
        ticklabels = ax.xaxis.get_ticklabels()
        for tk, tkl in zip(ticklines, ticklabels):
            #    tk.set_markersize(12)
            #tkl.set_fontsize(11)
            pass
        ticklines = ax.yaxis.get_ticklines()
        ticklabels = ax.yaxis.get_ticklabels()
        for tk, tkl in zip(ticklines, ticklabels):
            #    tk.set_markersize(12)
            #tkl.set_fontsize(11)
            pass
        plt.tight_layout()
        plt.savefig('{0}.pdf'.format(name))
    plt.show()

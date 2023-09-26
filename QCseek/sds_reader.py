import numpy as np
import cv2
from cv2_rolling_ball import subtract_background_rolling_ball
# import matplotlib.pyplot as plt
from scipy.signal import find_peaks


# test
def pre_cut(img, cut_bg: bool = False):
    '''图片预处理，裁剪，灰度化，背景减除'''
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 根据阈值二值化
    _, img_b = cv2.threshold(img_gray, 254, 255, cv2.THRESH_BINARY)
    row = np.array(img_b)
    # 统计纵向平均灰度值，确定胶孔边界
    row_mean = row.mean(axis=1)
    top = 0
    for i in range(len(row_mean)):
        if row_mean[i] < 5:
            top = i
            break
    # 裁剪胶孔
    img_gray = img_gray[top+10:, :]
    # 滑动抛物面算法减除背景
    if cut_bg:
        img_gray, _ = subtract_background_rolling_ball(
            img_gray, 30, use_paraboloid=True)
    # 灰度反转
    img_gray = np.ones(img_gray.shape, dtype=np.uint8)*255-np.array(img_gray)
    return img[top+10:, :], img_gray


# test
def gel_crop(img: np.ndarray) -> list:
    '''
    根据泳道裁剪图片
    img: 图片像素矩阵
    return: 返回切片列表
    '''
    # 平均校正算法
    # 1.均分，根据宽度15均分
    width = len(img[0])
    edges = [int((i+1)*width/15) for i in range(14)]
    # 2.校正1：横向灰度极值校正
    edges = gray_check(img, edges)
    # 3.校正2：空白泳道校正
    edges = blank_check(img, edges)

    # plt.imshow(img, cmap="gray")
    # plt.vlines(edges, 0, len(img), colors="red")
    # plt.show()

    # 边界列表
    lines = [0, *edges, width]
    return lines


def gray_check(img: np.ndarray, edges: list):
    '''横向灰度极值校正'''
    # 统计列平均灰度曲线
    img_inv = np.ones(img.shape, dtype=np.uint8)*255-np.array(img)
    col = np.array(img_inv)
    col_mean = col.mean(axis=0)

    # 查找峰顶，即分割界限
    peaks, _ = find_peaks(col_mean, height=245,
                          distance=len(img[0])/30, prominence=2)
    if len(peaks) == 0:
        return edges
    # plt.plot(np.arange(len(col_mean)), col_mean)
    # plt.plot(peaks, col_mean[peaks], "x")
    # plt.show()

    # 查找最近边界并校正
    for i, e in enumerate(edges):
        dis = [abs(e-p) for p in peaks]
        if min(dis) < len(img[0])/30:
            edges[i] = peaks[dis.index(min(dis))]
    # 返回校正度
    return edges


def blank_check(img: np.ndarray, edges: list):
    '''空白泳道校正'''
    # 阈值处理&灰度统计
    _, img_n = cv2.threshold(img, 50, 255, cv2.THRESH_BINARY)
    col = np.array(img_n)
    col_mean = col.mean(axis=0)
    # 计算临界零点
    zeros = []
    for i in range(1, len(col_mean)-1):
        if col_mean[i] == 0 and (col_mean[i+1] > 0 or col_mean[i-1] > 0):
            zeros.append(i)
    # 过滤空白边界
    blanks = []
    for i in range(len(zeros)):
        if i == 0:
            if (zeros[i+1]-zeros[i]) > len(img)/30:
                blanks.append(zeros[i])
        elif i == len(zeros)-1:
            if (zeros[i]-zeros[i-1]) > len(img)/30:
                blanks.append(zeros[i])
        else:
            if (zeros[i+1]-zeros[i]) > len(img)/30 and (zeros[i]-zeros[i-1]) > len(img)/30:
                blanks.append(zeros[i])
    if not blanks:
        return edges
    # 查找最近边界并校正
    for i, e in enumerate(edges):
        dis = [abs(e-b) for b in blanks]
        if min(dis) < len(img[0])/30:
            edges[i] = blanks[dis.index(min(dis))]
    # plt.plot(np.arange(len(col_mean)), col_mean)
    # plt.plot(blanks, col_mean[blanks], "x")
    # plt.show()
    return edges
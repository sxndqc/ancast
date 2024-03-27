import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
data = np.random.randint(10000, 100000, size=(5, 5))  # 生成5*5的随机五位数数字矩阵


plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False    # 解决保存图像是负号'-'显示为方块的问题

# 基于数据的最大值和最小值来计算颜色映射
norm = plt.Normalize(data.min(), data.max())
colors = plt.cm.viridis(norm(data))

def draw23():

    matrices = []
    matrices.append(np.array([[1, 0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]))
    matrices.append(np.array( [[0.9  ,   0.  ,   0.  ,   0 , 0.    ], 
    [0.  ,   0.134 , 0.134 , 0.134 , 0.1407] ,
    [0.  ,   0.134 , 0.134 , 0.134 , 0.1407],
    [0.1019 ,0.134 , 0.134 , 0.1535, 0.1407],
    [0.  ,   0.1407, 0.1407, 0.1407 ,0.1561]]))

    matrices.append(np.array([[ 1.1011 , 0.0002 , 0.0002 , 0.0206 , 0.0002],
    [ 0.0002 , 0.0270 , 0.0270 , 0.0270 , 0.0283],
    [ 0.0002 , 0.0270 , 0.1170 , 0.0270 , 0.0283],
    [ 0.0206 , 0.0270 , 0.0270  ,0.0309 , 0.0283],
    [ 0.0002 , 0.0283 , 0.0283 , 0.0283 , 0.1886]]))

    matrices.append(np.array([[1, 0,0,0,0],[0,0,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1]]))

    matrices.append(np.array([[1.  ,   0.  ,   0.  ,   0.1104 ,0.    ],
    [0.  ,   0.0966 ,0.0966 ,0.0966 ,0.1018],
    [0.  ,   0.0966 ,1.     ,0.0966 ,0.1018],
    [0.1104 ,0.0966 ,0.0966 ,1.     ,0.1018],
    [0. ,    0.1018 ,0.1018 ,0.1018 ,1.    ]]))
    matrices.append(np.array([[ 1.1011,  0.0002,  0.0002 , 0.0223 , 0.0002],
    [ 0.0002 , 0.0195 , 0.0195 , 0.0195 , 0.0206],
    [ 0.0002 , 0.0195 , 0.8675 , 0.0195  ,0.0206],
    [ 0.0223 , 0.0195 , 0.0195  ,0.2002 , 0.0206],
    [ 0.0002 , 0.0206 , 0.0206 , 0.0206 , 1.2012]]))

    # 绘制矩阵

    matrix_labels = ["read", "home", "she", "papaer", "i"]
    col_labels = ["read", "house", "he", "book", "i"]

    vmin = min(matrix.min() for matrix in matrices)
    vmax = max(matrix.max() for matrix in matrices)

    rows = 2
    cols = 3

    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(rows, cols, width_ratios=[1, 1, 1], wspace=0.3, hspace=0.15)

    label_fontsize = 8
    number_fontsize = 9

    for idx, matrix in enumerate(matrices):
        ax = fig.add_subplot(gs[idx])
        c = ax.imshow(matrix, vmin=vmin, vmax=vmax, aspect='auto', cmap='cividis')
        
        # 在矩阵中写上数字
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if idx % cols == 0:  # 第1个和第4个矩阵
                    text = str(int(matrix[i, j]))
                else:
                    text = f"{matrix[i, j]:.3f}"
                ax.text(j, i, text, ha="center", fontweight='bold', va="center", color="w" if matrix[i, j] < (vmax+vmin)/2 else "black", fontsize=number_fontsize)
        
        # 设置标签
        ax.set_yticks(np.arange(matrix.shape[0]))
        ax.set_yticklabels(matrix_labels, fontsize=label_fontsize)
        
        if idx < 3:  # 第一行
            ax.xaxis.tick_top()
            ax.set_xticks(np.arange(matrix.shape[1]))
            ax.set_xticklabels(col_labels, rotation=45, fontsize=label_fontsize)
        else:  # 第二行
            ax.set_xticks(np.arange(matrix.shape[1]))
            ax.set_xticklabels(col_labels, rotation=45, fontsize=label_fontsize)


    # 添加色条
    cbar_ax = fig.add_axes([0.95, 0.15, 0.02, 0.7])
    fig.colorbar(c, cax=cbar_ax)
    plt.savefig("myimg.svg", format="svg", bbox_inches='tight', pad_inches=0)
    plt.show()


def draw1():

    # 创建一个示例5*5矩阵
    matrix =  np.array([[0.9, 0,0,0 , 0],[0,0,0,0 , 0],[0,0,0.667,0, 0],[0,0,0,0 , 0],[0,0,0,0, 1]])

    label_fontsize = 8
    number_fontsize = 9
    # 设定每个5*5矩阵的标签
    matrix_labels = ["read", "home", "she", "papaer", "i"]
    col_labels = ["read", "house", "he", "book", "i"]

    fig, ax = plt.subplots()

    # 显示矩阵
    c = ax.imshow(matrix, aspect='auto', cmap='cividis')

    # 在矩阵中写上数字
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            text = f"{matrix[i, j]:.2f}"
            ax.text(j, i, text, ha="center", fontweight='bold', va="center", color="w" if matrix[i, j] < 0.5 else "black")

    # 设置标签
    ax.xaxis.tick_top()
    ax.set_xticks(np.arange(matrix.shape[1]))
    ax.set_yticks(np.arange(matrix.shape[0]))
    ax.set_xticklabels(col_labels, rotation=45)
    ax.set_yticklabels(matrix_labels)

    # 调整边缘
    fig.subplots_adjust(left=0.2, right=0.8, top=0.9, bottom=0.1)

    # 添加色条
    cbar_ax = fig.add_axes([0.85, 0.1, 0.02, 0.8])
    fig.colorbar(c, cax=cbar_ax)

    # 保存图像
    plt.savefig("single_matrix.svg",bbox_inches='tight', format="svg", pad_inches=0)

    # 显示图像
    plt.show()

if __name__ == "__main__":
    draw23()
   

#구현할 방향성 (제가 임의로 만든 겁니다. 추후 방향성으로..)
# 1. 한국/일본 작물별 정보 api/text parsing을 통해 가져오기
# 2. 데이터 정보 분석 밑 목적별 최적의 작물 추천

# 方向性
# 1. 韓国/日本の作物別情報を API やテキスト解析で取得する
# 2. データ情報を分析し目的別に最適な作物を推薦する

# app.py
import os
import io
import math
import base64
from collections import defaultdict

import neal
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, render_template, request

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-in-production')

# 作物設定
# spacing_row_cm は列間や畝間に相当
# spacing_col_cm は株間に相当

# 작물 설정
# spacing_row_cm은 열 간격이나 고랑 간격
# spacing_col_cm은 식물간 간격
# crop_key_1 : for comparing all the crops
crop_key_1 = ['rice', 'sweet_potato_early', 'sweet_potato_late', 'hakusai', 
              'daikon', 'lettuce', 'garlic', 'onion', 'negi', 'chili_open', 
              'chili_guide_1row', 'chili_guide_2row']

CROPS = {
    'rice': {
        'label': 'Rice (Transplanted)',
        'spacing_text': '30 x 14 to 15 cm',
        'spacing_row_cm': 30,
        'spacing_col_cm': 15,
    },
    'sweet_potato_early': {
        'label': 'Sweet Potato (Early or Normal Season)',
        'spacing_text': '70 to 75 x 20 cm',
        'spacing_row_cm': 75,
        'spacing_col_cm': 20,
    },
    'sweet_potato_late': {
        'label': 'Sweet Potato (Late Season)',
        'spacing_text': '75 x 25 cm',
        'spacing_row_cm': 75,
        'spacing_col_cm': 25,
    },
    'hakusai': {
        'label': 'Chinese Cabbage',
        'spacing_text': '60 to 70 x 30 to 40 cm',
        'spacing_row_cm': 70,
        'spacing_col_cm': 40,
    },
    'daikon': {
        'label': 'Daikon Radish',
        'spacing_text': '60 x 25 to 30 cm',
        'spacing_row_cm': 60,
        'spacing_col_cm': 30,
    },
    'lettuce': {
        'label': 'Lettuce',
        'spacing_text': '15 to 20 x 15 to 20 cm',
        'spacing_row_cm': 20,
        'spacing_col_cm': 20,
    },
    'garlic': {
        'label': 'Garlic',
        'spacing_text': '20 x 10 cm',
        'spacing_row_cm': 20,
        'spacing_col_cm': 10,
    },
    'onion': {
        'label': 'Onion',
        'spacing_text': '20 to 25 x 10 cm',
        'spacing_row_cm': 25,
        'spacing_col_cm': 10,
    },
    'negi': {
        'label': 'Japanese Long Onion',
        'spacing_text': '75 to 85 x 5 cm',
        'spacing_row_cm': 85,
        'spacing_col_cm': 5,
    },
    'chili_open': {
        'label': 'Chili Pepper (Open Field, Single Row)',
        'spacing_text': '100 to 110 x 35 cm',
        'spacing_row_cm': 110,
        'spacing_col_cm': 35,
    },
    'chili_guide_1row': {
        'label': 'Chili Pepper (Management Guide, 1 Row)',
        'spacing_text': 'Row width 90 to 100 cm',
        'spacing_row_cm': 100,
        'spacing_col_cm': 35,
    },
    'chili_guide_2row': {
        'label': 'Chili Pepper (Management Guide, 2 Rows)',
        'spacing_text': 'Two row width 150 to 160 cm',
        'spacing_row_cm': 160,
        'spacing_col_cm': 35,
    },
}

# QUBO 의 입력값 제한
# 밭의 가로/세로 최대 100m (10000cm)로 제한
# MAX_VARS : QUBO 변수 수 최대 1600개로 제한
MAX_DIM_CM = 10000
MAX_VARS = 1600

# 2차원 격자 위치를 1차원 index로 반환
def get_idx(r, c, w):
    return r * w + c

def choose_candidate_step(spacing_row_cm, spacing_col_cm, length_cm, width_cm):
    # 候補点の刻みを作物間隔の半分程度に設定して、
    # SAが配置を選べる余地を残す

    # 후보점(후보 위치) 간격을 작물 간격의 절반 정도로 설정해서, --> 작물간 간격 유지
    # SA(시뮬레이티드 어닐링)가 배치를 선택할 수 있는 여지를 남긴다
    step_r = max(5, int(round(spacing_row_cm / 2)))
    step_c = max(5, int(round(spacing_col_cm / 2)))

    #격자의 최소(1칸) 유지
    h = max(1, length_cm // step_r)
    w = max(1, width_cm // step_c)

    # 変数数が増えすぎる場合は自動で粗くする
    # 변수 개수가 너무 많아지는 경우에는 자동으로 (해상도를) 낮춰서 더 거칠게 만든다
    if h * w > MAX_VARS:
        scale  = math.sqrt((h * w) / MAX_VARS)
        step_r = max(5, int(math.ceil(step_r * scale)))
        step_c = max(5, int(math.ceil(step_c * scale)))
        h      = max(1, length_cm // step_r)
        w      = max(1, width_cm // step_c)

    return int(step_r), int(step_c), int(h), int(w)

def build_qubo(S, step_r, step_c, spacing_row_cm, spacing_col_cm):
    h, w = S.shape

    # 相互作用ありのQUBO
    # 目的
    # 1 できるだけ多く植える
    # 2 地力が高い場所を優先
    # 3 作物間隔に違反する近接配置には大きなペナルティ

    # 상호작용(항)이 있는 QUBO
    # 목적
    # 1) 가능한 한 많이 심기
    # 2) 지력이 높은 위치를 우선
    # 3) 작물 간격을 위반하는 근접 배치에는 큰 페널티를 부여
    Q = defaultdict(float)
    
    count_reward     = 8.0
    fertility_weight = 2.0
    p_conflict       = 35.0

    # 地力スコアを 0 から 1 に正規化
    # 지력 점수를 0~1 범위로 정규화
    s_min = float(S.min())
    s_max = float(S.max())
    if s_max - s_min < 1e-9:
        S_norm = np.zeros_like(S, dtype=float)
    else:
        S_norm = (S - s_min) / (s_max - s_min)

    # 対角項
    # 대각항
    # Ising Hamiltonian의 S_i에 대응하는 항
    # Q[(I,I)]는 변수 x_i에 곱해지는 계수 Q_ii를 나타낸다
    for r in range(h):
        for c in range(w):
            i = get_idx(r, c, w)
            Q[(i, i)] += -(count_reward + fertility_weight * float(S_norm[r, c]))
            # ==> my understand : 우리가 QUBO에 넣어서 알고자 하는 목적함수는 
            # 시그마(a_i*x_i)꼴이고 2차원 행렬로부터 이러한 1차원 목적함수를 만드는데 결국 
            # 고려되는 것이 이진 행렬의 제곱은 원본과 같다는 특성이 고려되어 Q[(i,i)]에만 값을 계산

    # 近接禁止の相互作用
    # しきい値未満なら同時に植えない
    # 長方形近傍で近接判定

    # 근접 금지 상호작용
    # 임계값(기준 거리) 미만이면 동시에 심지 않음
    # 직사각형 근방(이웃 영역)으로 근접 여부를 판단
    dr_limit = max(0, int(math.ceil(spacing_row_cm / step_r)) - 1)
    dc_limit = max(0, int(math.ceil(spacing_col_cm / step_c)) - 1)
#------------------------------------------------------------26.2.28
    for r in range(h):
        for c in range(w):
            i = get_idx(r, c, w)

            for dr in range(-dr_limit, dr_limit + 1):
                for dc in range(-dc_limit, dc_limit + 1):
                    if dr == 0 and dc == 0:
                        continue

                    rr = r + dr
                    cc = c + dc
                    if rr < 0 or rr >= h or cc < 0 or cc >= w:
                        continue

                    # 片側だけ追加
                    # 중복 방지 --> 상삼각 행렬 만들려는 목적
                    j = get_idx(rr, cc, w)
                    if j <= i:
                        continue

                    # 実距離ベースで判定
                    # 실거리 기준으로 판정
                    # and 조건 말고 or 조건으로도 해볼 필요 있을듯
                    if abs(dr) * step_r < spacing_row_cm and abs(dc) * step_c < spacing_col_cm:
                        Q[(i, j)] += p_conflict

    return Q

def solve_sa_and_plot(length_cm, width_cm, crop_key, seed=42, num_reads=120):
    crop = CROPS[crop_key]
    spacing_row_cm = int(crop['spacing_row_cm'])
    spacing_col_cm = int(crop['spacing_col_cm'])

    step_r, step_c, h, w = choose_candidate_step(
        spacing_row_cm=spacing_row_cm,
        spacing_col_cm=spacing_col_cm,
        length_cm=length_cm,
        width_cm=width_cm
    )

    rng = np.random.default_rng(seed)
    S = rng.integers(1, 11, size=(h, w), endpoint=False)

    Q = build_qubo(S, step_r, step_c, spacing_row_cm, spacing_col_cm)

    sampler = neal.SimulatedAnnealingSampler()
    sampleset = sampler.sample_qubo(Q, num_reads=num_reads)
    
    #최적의 해 도출
    best_sample = sampleset.first.sample
    best_energy = float(sampleset.first.energy)

    result_field = np.zeros((h, w), dtype=int)
    plant_count = 0

    planted_points = []
    for r in range(h):
        for c in range(w):
            idx = get_idx(r, c, w)
            if int(best_sample.get(idx, 0)) == 1:
                result_field[r, c] = 1
                plant_count += 1
                x_cm = (c + 0.5) * step_c
                y_cm = (r + 0.5) * step_r
                planted_points.append((x_cm, y_cm))

    # 参考値
    # 理想的な格子配置の単純概算
    # 참고값
    # 이상적 그리드(Grid) 배치를 가정한 단순 근사치
    simple_capacity = (length_cm // spacing_row_cm) * (width_cm // spacing_col_cm)

    # 可視化
    # 시각화
    fig_w = min(14, max(6, w * 0.45))
    fig_h = min(10, max(4, h * 0.45))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    extent = [0, w * step_c, h * step_r, 0]
    im = ax.imshow(S, cmap='YlGn', extent=extent, aspect='auto')

    # 히트맵 위에 숫자 표현
    # visiualize the numbers on the heatmap
    if h <= 20 and w <= 20:
        for r in range(h):
            for c in range(w):
                ax.text(
                    (c + 0.5) * step_c,
                    (r + 0.5) * step_r,
                    str(int(S[r, c])),
                    ha='center',
                    va='center',
                    fontsize=8
                )

    if planted_points:
        xs = [p[0] for p in planted_points]
        ys = [p[1] for p in planted_points]
        ax.scatter(xs, ys, s=60, marker='o', c='red')

    ax.set_title(
        f'Agricultural Optimization: {crop["label"]} , Number of plants: {plant_count}',
        fontsize=20
    )
    ax.set_xlabel('Horizontal direction[cm]',fontsize=20)
    ax.set_ylabel('Vertical direction[cm]',fontsize=20)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Soil quality score',fontsize=20)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=140)
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return {
        'crop_label': crop['label'],
        'spacing_text': crop['spacing_text'],
        'spacing_row_cm': spacing_row_cm,
        'spacing_col_cm': spacing_col_cm,
        'length_cm': length_cm,
        'width_cm': width_cm,
        'candidate_step_r_cm': step_r,
        'candidate_step_c_cm': step_c,
        'grid_h': h,
        'grid_w': w,
        'plant_count': int(plant_count),
        'simple_capacity': int(simple_capacity),
        'best_energy': best_energy,
        'plot_base64': image_base64,
    }

# 원본 고치기 싫어서 만든 함수. 모든 작물에 대해서 실행하는 함수.
def execute_all_crops(length_cm, width_cm, crop_key_list = crop_key_1 ,seed=42, num_reads=120):
    result_list = []
    area = length_cm * width_cm
    d_min = d_max = o_min = o_max = e_min = e_max = 0

    for crop_key in CROPS:
        crop = CROPS[crop_key]
        spacing_row_cm = int(crop['spacing_row_cm'])
        spacing_col_cm = int(crop['spacing_col_cm'])

        step_r, step_c, h, w = choose_candidate_step(
            spacing_row_cm = spacing_row_cm,
            spacing_col_cm = spacing_col_cm,
            length_cm      = length_cm,
            width_cm       = width_cm
        )
        rng = np.random.default_rng(seed)
        S = rng.integers(1, 11, size=(h, w), endpoint=False)

        Q = build_qubo(S, step_r, step_c, spacing_row_cm, spacing_col_cm)

        sampler = neal.SimulatedAnnealingSampler()
        sampleset = sampler.sample_qubo(Q, num_reads=num_reads)
        
        #최적의 해 도출
        best_sample = sampleset.first.sample
        best_energy = float(sampleset.first.energy)

        result_field = np.zeros((h, w), dtype=int)
        plant_count  = 0

        planted_points = []
        for r in range(h):
            for c in range(w):
                idx = get_idx(r, c, w)
                if int(best_sample.get(idx, 0)) == 1:
                    result_field[r, c] = 1
                    plant_count += 1
                    x_cm = (c + 0.5) * step_c
                    y_cm = (r + 0.5) * step_r
                    planted_points.append((x_cm, y_cm))

        simple_capacity = (length_cm // spacing_row_cm) * (width_cm // spacing_col_cm)
        density         = int(plant_count)/int(area)
        occunpancy      = int(plant_count)/int(simple_capacity)
        energy_per_crop = int(best_energy)/int(plant_count)

        if density   > d_max: d_max = density
        elif density < d_min: d_min = density
    
        if occunpancy   > o_max: o_max = occunpancy
        elif occunpancy < o_min: o_min = occunpancy
        
        if energy_per_crop   > e_max: e_max = energy_per_crop
        elif energy_per_crop < e_min: e_min = energy_per_crop

        rst1 = [d_max, d_min, o_max, o_min, e_max, e_min]
        result = {
            'crop_name': crop_key,
            'crop_label': crop['label'],
            'spacing_text': crop['spacing_text'],
            'spacing_row_cm': spacing_row_cm,
            'spacing_col_cm': spacing_col_cm,
            'length_cm': length_cm,
            'width_cm': width_cm,
            'candidate_step_r_cm': step_r,
            'candidate_step_c_cm': step_c,
            'grid_h': h,
            'grid_w': w,
            'plant_count': int(plant_count),
            'simple_capacity': int(simple_capacity),
            'best_energy': best_energy,
            'density': density,
            'occunpancy': occunpancy,
            'energy_per_crop': energy_per_crop
        }
        result_list.append(result)

    return result_list, rst1

# min_max -> [d_max, d_min, o_max, o_min, e_max, e_min]
def normalized_graph(length_cm, width_cm, result_list, min_max, crop_key_list=crop_key_1):
    area = length_cm * width_cm
    # initialize separate lists
    d_norm_list = []
    o_norm_list = []
    e_norm_list = []
    categories = []

    for n in range(len(crop_key_list)):
        d = result_list[n]['density']
        o = result_list[n]['occunpancy']
        e = result_list[n]['energy_per_crop']

        d_norm = (d - min_max[1])/(min_max[0] - min_max[1])
        o_norm = (o - min_max[3])/(min_max[2] - min_max[3])
        e_norm = (min_max[4] - e)/(min_max[4] - min_max[5])

        d_norm_list.append(d_norm)
        o_norm_list.append(o_norm)
        e_norm_list.append(e_norm)
        categories.append(result_list[n]['crop_name'])
    
    fig, axs = plt.subplots(3, 1, sharex=True)
    bar_a = axs[0].bar(categories, d_norm_list, color='blue')
    bar_b = axs[1].bar(categories, o_norm_list, color='orange')
    bar_c = axs[2].bar(categories, e_norm_list, color='green')

    axs[0].bar_label(bar_a, fmt='%.2f', padding=3)
    axs[1].bar_label(bar_b, fmt='%.2f', padding=3)
    axs[2].bar_label(bar_c, fmt='%.2f', padding=3)
    
    axs[0].set_title('Normalized Density',fontsize = 15)
    axs[1].set_title('Normalized Occupancy(K/N)'    ,fontsize = 15)
    axs[2].set_title('Normalized E/K'               ,fontsize = 15)
    axs[0].set_ylabel('plants/㎡'        ,fontsize = 15)
    axs[1].set_ylabel('K/N'              ,fontsize = 15)
    axs[2].set_ylabel('E/K'              ,fontsize = 15)
    axs[2].set_xlabel('case'             ,fontsize = 15)
    axs[2].tick_params(axis='x'          ,labelrotation=30)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=140)
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return image_base64


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None

    default_values = {
        'length_cm': 300,
        'width_cm': 200,
        'crop_key': 'rice',
    }

    if request.method == 'POST':
        try:
            length_cm = int(request.form.get('length_cm', '').strip())
            width_cm = int(request.form.get('width_cm', '').strip())
            crop_key = request.form.get('crop_key', 'rice')

            if crop_key not in CROPS:
                raise ValueError('The crop selection is invalid.')

            if length_cm <= 0 or width_cm <= 0:
                raise ValueError('Please enter positive integers for the width and height.')

            if length_cm > MAX_DIM_CM or width_cm > MAX_DIM_CM:
                raise ValueError(f'Please enter the length and width in {MAX_DIM_CM} cm or less')

            #result = solve_sa_and_plot(length_cm, width_cm, crop_key)
            result_list, rst1 = execute_all_crops(length_cm, width_cm)
            result = normalized_graph(length_cm, width_cm, result_list, rst1)

            default_values = {
                'length_cm': length_cm,
                'width_cm': width_cm,
                'crop_key': crop_key,
            }

        except Exception as e:
            error = f'An error occurred in the input or calculation {e}'

    return render_template(
        #'index.html',
        'index_2.html',
        crops=CROPS,
        result=result,
        error=error,
        values=default_values
    )

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(host='0.0.0.0', port=port, debug=False)
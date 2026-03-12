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

MAX_DIM_CM = 10000
MAX_VARS = 1600

def get_idx(r, c, w):
    return r * w + c

def choose_candidate_step(spacing_row_cm, spacing_col_cm, length_cm, width_cm):
    # 候補点の刻みを作物間隔の半分程度に設定して、
    # SAが配置を選べる余地を残す
    step_r = max(5, int(round(spacing_row_cm / 2)))
    step_c = max(5, int(round(spacing_col_cm / 2)))

    h = max(1, length_cm // step_r)
    w = max(1, width_cm // step_c)

    # 変数数が増えすぎる場合は自動で粗くする
    if h * w > MAX_VARS:
        scale = math.sqrt((h * w) / MAX_VARS)
        step_r = max(5, int(math.ceil(step_r * scale)))
        step_c = max(5, int(math.ceil(step_c * scale)))
        h = max(1, length_cm // step_r)
        w = max(1, width_cm // step_c)

    return int(step_r), int(step_c), int(h), int(w)

def build_qubo(S, step_r, step_c, spacing_row_cm, spacing_col_cm):
    h, w = S.shape

    # 相互作用ありのQUBO
    # 目的
    # 1 できるだけ多く植える
    # 2 地力が高い場所を優先
    # 3 作物間隔に違反する近接配置には大きなペナルティ
    Q = defaultdict(float)

    count_reward = 8.0
    fertility_weight = 2.0
    p_conflict = 35.0

    # 地力スコアを 0 から 1 に正規化
    s_min = float(S.min())
    s_max = float(S.max())
    if s_max - s_min < 1e-9:
        S_norm = np.zeros_like(S, dtype=float)
    else:
        S_norm = (S - s_min) / (s_max - s_min)

    # 対角項
    for r in range(h):
        for c in range(w):
            i = get_idx(r, c, w)
            Q[(i, i)] += -(count_reward + fertility_weight * float(S_norm[r, c]))

    # 近接禁止の相互作用
    # しきい値未満なら同時に植えない
    # 長方形近傍で近接判定
    dr_limit = max(0, int(math.ceil(spacing_row_cm / step_r)) - 1)
    dc_limit = max(0, int(math.ceil(spacing_col_cm / step_c)) - 1)

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
                    j = get_idx(rr, cc, w)
                    if j <= i:
                        continue

                    # 実距離ベースで判定
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
    simple_capacity = (length_cm // spacing_row_cm) * (width_cm // spacing_col_cm)

    # 可視化
    fig_w = min(14, max(6, w * 0.45))
    fig_h = min(10, max(4, h * 0.45))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    extent = [0, w * step_c, h * step_r, 0]
    im = ax.imshow(S, cmap='YlGn', extent=extent, aspect='auto')

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

            result = solve_sa_and_plot(length_cm, width_cm, crop_key)

            default_values = {
                'length_cm': length_cm,
                'width_cm': width_cm,
                'crop_key': crop_key,
            }

        except Exception as e:
            error = f'An error occurred in the input or calculation {e}'

    return render_template(
        'index.html',
        crops=CROPS,
        result=result,
        error=error,
        values=default_values
    )

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(host='0.0.0.0', port=port, debug=False)
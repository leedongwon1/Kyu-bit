"""
QUBO 구성 + Simulated Annealing 최적화 핵심 로직
"""

import io
import math
import base64
from collections import defaultdict

import neal
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from crops_data import CROPS

MAX_VARS = 1600


# ── 유틸리티 ──

def get_idx(r: int, c: int, w: int) -> int:
    """2차원 격자 좌표 → 1차원 인덱스"""
    return r * w + c


def choose_candidate_step(spacing_row_cm, spacing_col_cm, length_cm, width_cm):
    """
    후보점 간격 계산.
    작물 간격의 절반 정도로 설정하여 SA가 배치를 선택할 여지를 남김.
    변수 수가 MAX_VARS를 초과하면 자동으로 해상도를 낮춤.
    """
    step_r = max(5, int(round(spacing_row_cm / 2)))
    step_c = max(5, int(round(spacing_col_cm / 2)))
    h = max(1, length_cm // step_r)
    w = max(1, width_cm  // step_c)

    if h * w > MAX_VARS:
        scale  = math.sqrt((h * w) / MAX_VARS)
        step_r = max(5, int(math.ceil(step_r * scale)))
        step_c = max(5, int(math.ceil(step_c * scale)))
        h = max(1, length_cm // step_r)
        w = max(1, width_cm  // step_c)

    return int(step_r), int(step_c), int(h), int(w)


# ── QUBO 행렬 생성 ──

def build_qubo(S, step_r, step_c, spacing_row_cm, spacing_col_cm):
    """
    QUBO 행렬 생성.
    - 대각항: 가능한 한 많이 심기 + 지력 높은 곳 우선
    - 비대각항: 작물 간격 위반 시 페널티
    """
    h, w = S.shape
    Q = defaultdict(float)

    count_reward     = 8.0
    fertility_weight = 2.0
    p_conflict       = 35.0

    s_min, s_max = float(S.min()), float(S.max())
    if s_max - s_min < 1e-9:
        S_norm = np.zeros_like(S, dtype=float)
    else:
        S_norm = (S - s_min) / (s_max - s_min)

    # 대각항
    for r in range(h):
        for c in range(w):
            i = get_idx(r, c, w)
            Q[(i, i)] += -(count_reward + fertility_weight * float(S_norm[r, c]))

    # 비대각항: 근접 금지
    dr_limit = max(0, int(math.ceil(spacing_row_cm / step_r)) - 1)
    dc_limit = max(0, int(math.ceil(spacing_col_cm / step_c)) - 1)

    for r in range(h):
        for c in range(w):
            i = get_idx(r, c, w)
            for dr in range(-dr_limit, dr_limit + 1):
                for dc in range(-dc_limit, dc_limit + 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if rr < 0 or rr >= h or cc < 0 or cc >= w:
                        continue
                    j = get_idx(rr, cc, w)
                    if j <= i:
                        continue
                    if abs(dr) * step_r < spacing_row_cm and abs(dc) * step_c < spacing_col_cm:
                        Q[(i, j)] += p_conflict

    return Q


# ── 단일 작물 최적화 ──

def solve_sa_single(length_cm, width_cm, crop_key, seed=42, num_reads=120):
    """단일 작물 SA 최적화 + 히트맵 시각화"""
    crop = CROPS[crop_key]
    spacing_row_cm = int(crop['spacing_row_cm'])
    spacing_col_cm = int(crop['spacing_col_cm'])

    step_r, step_c, h, w = choose_candidate_step(
        spacing_row_cm, spacing_col_cm, length_cm, width_cm
    )

    rng = np.random.default_rng(seed)
    S = rng.integers(1, 11, size=(h, w), endpoint=False)

    Q = build_qubo(S, step_r, step_c, spacing_row_cm, spacing_col_cm)
    sampler = neal.SimulatedAnnealingSampler()
    sampleset = sampler.sample_qubo(Q, num_reads=num_reads)

    best_sample = sampleset.first.sample
    best_energy = float(sampleset.first.energy)

    plant_count = 0
    planted_points = []
    for r in range(h):
        for c in range(w):
            if int(best_sample.get(get_idx(r, c, w), 0)) == 1:
                plant_count += 1
                planted_points.append({
                    "x_cm": round((c + 0.5) * step_c, 2),
                    "y_cm": round((r + 0.5) * step_r, 2),
                })

    simple_capacity = (length_cm // spacing_row_cm) * (width_cm // spacing_col_cm)

    # ── 시각화 ──
    fig_w = min(14, max(6, w * 0.45))
    fig_h = min(10, max(4, h * 0.45))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    extent = [0, w * step_c, h * step_r, 0]
    im = ax.imshow(S, cmap='YlGn', extent=extent, aspect='auto')

    if h <= 20 and w <= 20:
        for r in range(h):
            for c in range(w):
                ax.text(
                    (c + 0.5) * step_c, (r + 0.5) * step_r,
                    str(int(S[r, c])),
                    ha='center', va='center', fontsize=8,
                )

    if planted_points:
        xs = [p["x_cm"] for p in planted_points]
        ys = [p["y_cm"] for p in planted_points]
        ax.scatter(xs, ys, s=60, marker='o', c='red')

    ax.set_title(f'{crop["label"]} — Plants: {plant_count}', fontsize=16)
    ax.set_xlabel('Horizontal [cm]', fontsize=14)
    ax.set_ylabel('Vertical [cm]', fontsize=14)
    fig.colorbar(im, ax=ax).set_label('Soil quality', fontsize=14)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=140)
    plt.close(fig)
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.read()).decode('utf-8')

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
        'planted_points': planted_points,
        'plot_base64': plot_base64,
    }


# ── 전체 작물 비교 ──

def execute_all_crops(length_cm, width_cm, seed=42, num_reads=120):
    """12종 작물 일괄 SA 최적화"""
    result_list = []
    area = length_cm * width_cm

    for crop_key, crop in CROPS.items():
        spacing_row_cm = int(crop['spacing_row_cm'])
        spacing_col_cm = int(crop['spacing_col_cm'])

        step_r, step_c, h, w = choose_candidate_step(
            spacing_row_cm, spacing_col_cm, length_cm, width_cm
        )

        rng = np.random.default_rng(seed)
        S = rng.integers(1, 11, size=(h, w), endpoint=False)
        Q = build_qubo(S, step_r, step_c, spacing_row_cm, spacing_col_cm)

        sampler = neal.SimulatedAnnealingSampler()
        sampleset = sampler.sample_qubo(Q, num_reads=num_reads)

        best_sample = sampleset.first.sample
        best_energy = float(sampleset.first.energy)

        plant_count = sum(
            1 for r in range(h) for c in range(w)
            if int(best_sample.get(get_idx(r, c, w), 0)) == 1
        )

        simple_capacity = (length_cm // spacing_row_cm) * (width_cm // spacing_col_cm)
        density         = plant_count / area if area > 0 else 0
        occupancy       = plant_count / simple_capacity if simple_capacity > 0 else 0
        energy_per_crop = best_energy / plant_count if plant_count > 0 else 0

        result_list.append({
            'crop_name': crop_key,
            'crop_label': crop['label'],
            'spacing_text': crop['spacing_text'],
            'spacing_row_cm': spacing_row_cm,
            'spacing_col_cm': spacing_col_cm,
            'plant_count': int(plant_count),
            'simple_capacity': int(simple_capacity),
            'best_energy': best_energy,
            'density': density,
            'occupancy': occupancy,
            'energy_per_crop': energy_per_crop,
        })

    return result_list
"""
12종 작물 데이터 정의
spacing_row_cm: 열 간격 (고랑 간격)
spacing_col_cm: 주 간격 (식물 간 간격)
"""

CROPS = {
    'rice': {
        'label': 'Rice (Transplanted)',
        'label_kr': '벼 (이앙)',
        'emoji': '🌾',
        'spacing_text': '30 × 14~15 cm',
        'spacing_row_cm': 30,
        'spacing_col_cm': 15,
    },
    'sweet_potato_early': {
        'label': 'Sweet Potato (Early/Normal)',
        'label_kr': '고구마 (조기/보통)',
        'emoji': '🍠',
        'spacing_text': '70~75 × 20 cm',
        'spacing_row_cm': 75,
        'spacing_col_cm': 20,
    },
    'sweet_potato_late': {
        'label': 'Sweet Potato (Late Season)',
        'label_kr': '고구마 (만기)',
        'emoji': '🍠',
        'spacing_text': '75 × 25 cm',
        'spacing_row_cm': 75,
        'spacing_col_cm': 25,
    },
    'hakusai': {
        'label': 'Chinese Cabbage',
        'label_kr': '배추',
        'emoji': '🥬',
        'spacing_text': '60~70 × 30~40 cm',
        'spacing_row_cm': 70,
        'spacing_col_cm': 40,
    },
    'daikon': {
        'label': 'Daikon Radish',
        'label_kr': '무',
        'emoji': '🥕',
        'spacing_text': '60 × 25~30 cm',
        'spacing_row_cm': 60,
        'spacing_col_cm': 30,
    },
    'lettuce': {
        'label': 'Lettuce',
        'label_kr': '상추',
        'emoji': '🥗',
        'spacing_text': '15~20 × 15~20 cm',
        'spacing_row_cm': 20,
        'spacing_col_cm': 20,
    },
    'garlic': {
        'label': 'Garlic',
        'label_kr': '마늘',
        'emoji': '🧄',
        'spacing_text': '20 × 10 cm',
        'spacing_row_cm': 20,
        'spacing_col_cm': 10,
    },
    'onion': {
        'label': 'Onion',
        'label_kr': '양파',
        'emoji': '🧅',
        'spacing_text': '20~25 × 10 cm',
        'spacing_row_cm': 25,
        'spacing_col_cm': 10,
    },
    'negi': {
        'label': 'Japanese Long Onion',
        'label_kr': '대파',
        'emoji': '🥬',
        'spacing_text': '75~85 × 5 cm',
        'spacing_row_cm': 85,
        'spacing_col_cm': 5,
    },
    'chili_open': {
        'label': 'Chili Pepper (Open Field)',
        'label_kr': '고추 (노지 단줄)',
        'emoji': '🌶️',
        'spacing_text': '100~110 × 35 cm',
        'spacing_row_cm': 110,
        'spacing_col_cm': 35,
    },
    'chili_guide_1row': {
        'label': 'Chili Pepper (Guide, 1 Row)',
        'label_kr': '고추 (관리 1줄)',
        'emoji': '🌶️',
        'spacing_text': '90~100 × 35 cm',
        'spacing_row_cm': 100,
        'spacing_col_cm': 35,
    },
    'chili_guide_2row': {
        'label': 'Chili Pepper (Guide, 2 Rows)',
        'label_kr': '고추 (관리 2줄)',
        'emoji': '🌶️',
        'spacing_text': '150~160 × 35 cm',
        'spacing_row_cm': 160,
        'spacing_col_cm': 35,
    },
}
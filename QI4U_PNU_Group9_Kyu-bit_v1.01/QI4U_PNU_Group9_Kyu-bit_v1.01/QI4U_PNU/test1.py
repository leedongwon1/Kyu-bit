import matplotlib.pyplot as plt
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


categories = ['a', 'b', 'c']
d_norm_list = [1, 2, 3]
o_norm_list = [4,5,6]
e_norm_list = [7,8,9]
plt.bar(categories, d_norm_list, color='blue')
plt.title('d_norm')
plt.xlabel('categories')
plt.ylabel('number')
#plt.show()

plt.bar(categories, o_norm_list, color='orange')
plt.title('o_norm')
plt.xlabel('categories')
plt.ylabel('number')
#plt.show()

plt.bar(categories, e_norm_list, color='green')
plt.title('e_norm')
plt.xlabel('categories')
plt.ylabel('number')
#plt.show()
plt.show()
"""
=============================================================
  Resilience Profiler — ML Model Training & Comparison
  Навчання моделей машинного навчання на синтетичних даних
  
  Автор: Головач І. М., гр. ІН.мз-51с, СумДУ, 2026
=============================================================

Запуск:
    pip install scikit-learn xgboost matplotlib pandas seaborn
    python ml_training.py
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score, learning_curve
from sklearn.metrics import (accuracy_score, f1_score,
                             classification_report, confusion_matrix)
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

# ─────────────────────────────────────────────────────────
# 1. ГЕНЕРАЦІЯ СИНТЕТИЧНОГО ДАТАСЕТУ
# ─────────────────────────────────────────────────────────

print("=" * 60)
print("  RESILIENCE PROFILER — ML TRAINING")
print("=" * 60)
print()
print("📊 Крок 1: Генерація синтетичного датасету...")

np.random.seed(42)

# 5 субшкал × 5 питань = 25 ознак
SCALES = [
    'Емоційна регуляція',
    'Когнітивна гнучкість',
    'Соціальна підтримка',
    'Самоефективність',
    'Осмислення досвіду',
]
LEVELS = ['Low', 'Moderate', 'High']

# Профілі відповідей для кожного рівня резильєнтності
PROFILES = {
    0: {'means': [2.0, 2.2, 1.8, 2.1, 1.9], 'std': 0.75},   # Low
    1: {'means': [3.2, 3.5, 2.9, 3.8, 3.3], 'std': 0.80},   # Moderate
    2: {'means': [4.3, 4.4, 4.2, 4.6, 4.3], 'std': 0.60},   # High
}

def generate_dataset(n_per_class=200):
    """Генерує синтетичний датасет із реалістичними профілями."""
    X_list, y_list = [], []

    for level, profile in PROFILES.items():
        for _ in range(n_per_class):
            row = []
            for scale_mean in profile['means']:
                answers = np.random.normal(scale_mean, profile['std'], 5)
                answers = np.clip(np.round(answers), 1, 5)
                row.extend(answers.tolist())
            X_list.append(row)
            y_list.append(level)

    X = np.array(X_list, dtype=float)
    y = np.array(y_list)
    return X, y

X, y = generate_dataset(n_per_class=200)

# Назви ознак
feature_names = [
    f'{scale}_Q{q}'
    for scale in ['Ем.рег.', 'Когн.гнучк.', 'Соц.підтр.', 'Самоеф.', 'Осм.досв.']
    for q in range(1, 6)
]

# DataFrame для зручного аналізу
df = pd.DataFrame(X, columns=feature_names)
df['level'] = [LEVELS[l] for l in y]

print(f"   Розмір датасету: {X.shape[0]} прикладів × {X.shape[1]} ознак")
print(f"   Класи: " + ", ".join(f"{l}={sum(y==i)}" for i, l in enumerate(LEVELS)))
print(f"   Середні значення по рівнях:")
for i, lvl in enumerate(LEVELS):
    mask = y == i
    scale_means = [X[mask, s*5:(s+1)*5].mean() for s in range(5)]
    print(f"     {lvl}: " + " | ".join(f"{SCALES[s][:8]}={scale_means[s]:.2f}" for s in range(5)))
print()

# ─────────────────────────────────────────────────────────
# 2. ПОДІЛ НА TRAIN/TEST
# ─────────────────────────────────────────────────────────

print("📊 Крок 2: Поділ train/test (80/20)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Нормалізація (потрібна для MLP)
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

print(f"   Train: {len(X_train)}, Test: {len(X_test)}")
print()

# ─────────────────────────────────────────────────────────
# 3. НАВЧАННЯ МОДЕЛЕЙ
# ─────────────────────────────────────────────────────────

print("🤖 Крок 3: Навчання моделей...")
print()

models_config = [
    {
        'name': 'Random Forest',
        'model': RandomForestClassifier(n_estimators=100, random_state=42),
        'scaled': False,
        'color': '#378ADD',
    },
    {
        'name': 'XGBoost',
        'model': XGBClassifier(
            n_estimators=100, random_state=42,
            eval_metric='mlogloss', verbosity=0
        ),
        'scaled': False,
        'color': '#534AB7',
    },
    {
        'name': 'MLP (нейромережа)',
        'model': MLPClassifier(
            hidden_layer_sizes=(64, 32),
            max_iter=500, random_state=42
        ),
        'scaled': True,
        'color': '#1D9E75',
    },
]

results = {}

for cfg in models_config:
    name  = cfg['name']
    model = cfg['model']
    Xtr   = X_train_sc if cfg['scaled'] else X_train
    Xte   = X_test_sc  if cfg['scaled'] else X_test

    model.fit(Xtr, y_train)
    y_pred = model.predict(Xte)

    acc = accuracy_score(y_test, y_pred)
    f1  = f1_score(y_test, y_pred, average='weighted')
    cv  = cross_val_score(model, Xtr, y_train, cv=5, scoring='accuracy')

    results[name] = {
        'model':   model,
        'y_pred':  y_pred,
        'acc':     acc,
        'f1':      f1,
        'cv_mean': cv.mean(),
        'cv_std':  cv.std(),
        'color':   cfg['color'],
        'scaled':  cfg['scaled'],
    }

    print(f"   ✅ {name}")
    print(f"      Accuracy:  {acc*100:.2f}%")
    print(f"      F1-score:  {f1*100:.2f}%")
    print(f"      CV (5-fold): {cv.mean()*100:.2f}% ± {cv.std()*100:.2f}%")
    print()

# ─────────────────────────────────────────────────────────
# 4. FEATURE IMPORTANCE
# ─────────────────────────────────────────────────────────

print("📊 Крок 4: Аналіз важливості ознак...")

rf_imp  = results['Random Forest']['model'].feature_importances_
xgb_imp = results['XGBoost']['model'].feature_importances_

# По субшкалах
scale_rf  = [rf_imp[i*5:(i+1)*5].sum()  for i in range(5)]
scale_xgb = [xgb_imp[i*5:(i+1)*5].sum() for i in range(5)]

print("   Топ субшкал (RF):")
for i in np.argsort(scale_rf)[::-1]:
    print(f"     {SCALES[i]:<25}: {scale_rf[i]*100:.1f}%")
print("   Топ субшкал (XGBoost):")
for i in np.argsort(scale_xgb)[::-1]:
    print(f"     {SCALES[i]:<25}: {scale_xgb[i]*100:.1f}%")
print()

# ─────────────────────────────────────────────────────────
# 5. CLASSIFICATION REPORTS
# ─────────────────────────────────────────────────────────

print("📋 Крок 5: Детальні звіти класифікації")
print()
for name, r in results.items():
    print(f"   [{name}]")
    report = classification_report(y_test, r["y_pred"], target_names=LEVELS)
    for line in report.split("\n"):
        print("      " + line)

# ─────────────────────────────────────────────────────────
# 6. ВІЗУАЛІЗАЦІЯ
# ─────────────────────────────────────────────────────────

print("📈 Крок 6: Побудова графіків...")

plt.style.use('seaborn-v0_8-whitegrid')
fig = plt.figure(figsize=(18, 14))
fig.suptitle(
    'Resilience Profiler — Порівняння алгоритмів МН\n'
    'Синтетичний датасет: 600 прикладів, 25 ознак (5 субшкал × 5 питань)',
    fontsize=14, fontweight='bold', y=0.98
)

model_names  = list(results.keys())
model_colors = [results[n]['color'] for n in model_names]
acc_vals     = [results[n]['acc']*100    for n in model_names]
f1_vals      = [results[n]['f1']*100     for n in model_names]
cv_means     = [results[n]['cv_mean']*100 for n in model_names]
cv_stds      = [results[n]['cv_std']*100  for n in model_names]

x = np.arange(len(model_names))
w = 0.3

# ── ГРАФІК 1: Accuracy + F1 ──────────────────────────────
ax1 = fig.add_subplot(3, 3, 1)
bars1 = ax1.bar(x - w/2, acc_vals, w, label='Accuracy', color=model_colors, alpha=0.9)
bars2 = ax1.bar(x + w/2, f1_vals,  w, label='F1-score', color=model_colors, alpha=0.5,
                edgecolor=model_colors, linewidth=1.5)
ax1.set_ylim(85, 102)
ax1.set_xticks(x)
ax1.set_xticklabels(['RF', 'XGBoost', 'MLP'], fontsize=10)
ax1.set_ylabel('Точність, %')
ax1.set_title('Accuracy та F1-score', fontsize=11, fontweight='bold')
ax1.legend(fontsize=9)
for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

# ── ГРАФІК 2: CV з довірчим інтервалом ──────────────────
ax2 = fig.add_subplot(3, 3, 2)
bars = ax2.bar(x, cv_means, color=model_colors, alpha=0.85,
               yerr=cv_stds, capsize=6, error_kw={'linewidth': 2})
ax2.set_ylim(85, 102)
ax2.set_xticks(x)
ax2.set_xticklabels(['RF', 'XGBoost', 'MLP'], fontsize=10)
ax2.set_ylabel('Точність, %')
ax2.set_title('5-fold Cross-Validation (mean ± std)', fontsize=11, fontweight='bold')
for bar, mean, std in zip(bars, cv_means, cv_stds):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + std + 0.5,
             f'{mean:.1f}%\n±{std:.1f}%', ha='center', va='bottom', fontsize=8)

# ── ГРАФІК 3: Зведена таблиця ────────────────────────────
ax3 = fig.add_subplot(3, 3, 3)
ax3.axis('off')
table_data = [
    ['Метрика', 'RF', 'XGBoost', 'MLP'],
    ['Accuracy', f'{acc_vals[0]:.1f}%', f'{acc_vals[1]:.1f}%★', f'{acc_vals[2]:.1f}%'],
    ['F1-score', f'{f1_vals[0]:.1f}%',  f'{f1_vals[1]:.1f}%★',  f'{f1_vals[2]:.1f}%'],
    ['CV mean',  f'{cv_means[0]:.1f}%', f'{cv_means[1]:.1f}%',  f'{cv_means[2]:.1f}%'],
    ['CV std',   f'±{cv_stds[0]:.1f}%',f'±{cv_stds[1]:.1f}%', f'±{cv_stds[2]:.1f}%'],
    ['Інтерпрет.',  'Висока★', 'SHAP', 'Низька'],
    ['Перенавч.',   'Стійкий★','Стійкий','Середнє'],
    ['Час навч.',   'Швидкий', 'Швидкий','Повільний'],
]
tbl = ax3.table(
    cellText=table_data[1:],
    colLabels=table_data[0],
    cellLoc='center', loc='center',
    bbox=[0, 0, 1, 1]
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_facecolor('#1A1035')
        cell.set_text_props(color='white', fontweight='bold')
    elif '★' in cell.get_text().get_text():
        cell.set_facecolor('#EEEDFE')
        cell.set_text_props(color='#3C3489', fontweight='bold')
    elif r % 2 == 0:
        cell.set_facecolor('#F5F3FF')
    cell.set_edgecolor('#CCCCCC')
ax3.set_title('Зведена таблиця результатів', fontsize=11, fontweight='bold', pad=10)

# ── ГРАФІК 4: Матриця помилок — RF ───────────────────────
for idx, name in enumerate(model_names):
    ax = fig.add_subplot(3, 3, 4 + idx)
    cm = confusion_matrix(y_test, results[name]['y_pred'])
    sns.heatmap(cm, annot=True, fmt='d', ax=ax,
                xticklabels=LEVELS, yticklabels=LEVELS,
                cmap='Blues', cbar=False,
                linewidths=0.5, linecolor='white')
    ax.set_title(f'Матриця помилок — {name}', fontsize=10, fontweight='bold')
    ax.set_ylabel('Справжній клас')
    ax.set_xlabel('Передбачений клас')
    ax.tick_params(labelsize=9)

# ── ГРАФІК 7: Feature importance RF (субшкали) ───────────
ax7 = fig.add_subplot(3, 3, 7)
colors_scales = ['#E74C3C', '#534AB7', '#27AE60', '#E67E22', '#2980B9']
bars_rf = ax7.barh(SCALES, [v*100 for v in scale_rf], color=colors_scales, alpha=0.85)
ax7.set_xlabel('Важливість, %')
ax7.set_title('Feature Importance — Random Forest\n(за субшкалами)', fontsize=10, fontweight='bold')
ax7.tick_params(labelsize=9)
for bar in bars_rf:
    ax7.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
             f'{bar.get_width():.1f}%', va='center', fontsize=9)

# ── ГРАФІК 8: Feature importance XGBoost ─────────────────
ax8 = fig.add_subplot(3, 3, 8)
bars_xgb = ax8.barh(SCALES, [v*100 for v in scale_xgb], color=colors_scales, alpha=0.85)
ax8.set_xlabel('Важливість, %')
ax8.set_title('Feature Importance — XGBoost\n(за субшкалами)', fontsize=10, fontweight='bold')
ax8.tick_params(labelsize=9)
for bar in bars_xgb:
    ax8.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
             f'{bar.get_width():.1f}%', va='center', fontsize=9)

# ── ГРАФІК 9: Криві навчання ──────────────────────────────
ax9 = fig.add_subplot(3, 3, 9)
for cfg in models_config:
    name  = cfg['name']
    model = cfg['model']
    Xtr   = X_train_sc if cfg['scaled'] else X_train
    sizes, train_sc, val_sc = learning_curve(
        model, Xtr, y_train,
        train_sizes=np.linspace(0.1, 1.0, 7),
        cv=5, n_jobs=-1
    )
    label = name.replace(' (нейромережа)', '')
    ax9.plot(sizes, val_sc.mean(axis=1)*100,
             label=label, color=cfg['color'],
             marker='o', markersize=4,
             linewidth=2,
             linestyle='--' if 'MLP' in name else '-')

ax9.set_xlabel('Розмір навчальної вибірки')
ax9.set_ylabel('Точність, %')
ax9.set_title('Криві навчання (CV validation)', fontsize=10, fontweight='bold')
ax9.legend(fontsize=9)
ax9.set_ylim(75, 102)
ax9.tick_params(labelsize=9)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('ml_results.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.show()
print()
print("✅ Графік збережено: ml_results.png")

# ─────────────────────────────────────────────────────────
# 7. ЗБЕРЕЖЕННЯ МОДЕЛІ
# ─────────────────────────────────────────────────────────

print()
print("💾 Крок 7: Збереження найкращої моделі (XGBoost)...")

import pickle

best_model = results['XGBoost']['model']
with open('resilience_model.pkl', 'wb') as f:
    pickle.dump({'model': best_model, 'scaler': scaler}, f)

print("   Модель збережено: resilience_model.pkl")

# ─────────────────────────────────────────────────────────
# 8. ТЕСТ ПЕРЕДБАЧЕННЯ (приклад)
# ─────────────────────────────────────────────────────────

print()
print("🔍 Крок 8: Тест передбачення для нового користувача...")

# Приклад відповідей (помірна резильєнтність)
sample_answers = np.array([[
    3, 3, 4, 3, 3,   # Емоційна регуляція
    4, 3, 4, 4, 3,   # Когнітивна гнучкість
    2, 2, 3, 2, 1,   # Соціальна підтримка (слабка)
    4, 5, 4, 3, 5,   # Самоефективність (сильна)
    5, 4, 5, 5, 4,   # Осмислення досвіду (сильне)
]], dtype=float)

for name, r in results.items():
    model = r['model']
    X_inp = scaler.transform(sample_answers) if r['scaled'] else sample_answers
    pred  = model.predict(X_inp)[0]
    prob  = model.predict_proba(X_inp)[0]
    print(f"   {name:<22}: {LEVELS[pred]:<10} "
          f"(Low={prob[0]*100:.0f}%, Mod={prob[1]*100:.0f}%, High={prob[2]*100:.0f}%)")

print()
print("=" * 60)
print("  ✅ НАВЧАННЯ ЗАВЕРШЕНО УСПІШНО")
print(f"  Найкраща модель: XGBoost (Accuracy={results['XGBoost']['acc']*100:.1f}%)")
print("=" * 60)

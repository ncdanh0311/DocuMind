import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Cau hinh ve hinh chuan Paper
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.style.use('seaborn-v0_8-paper')
OUTPUT_DIR = "results/research_report"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_trainer_state(json_path, model_name):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    history = data.get('log_history', [])
    rows = []
    for log in history:
        # Lay cac metric quan trong
        row = {
            'model': model_name,
            'epoch': log.get('epoch'),
            'step': log.get('step'),
            'train_loss': log.get('loss'),
            'val_loss': log.get('eval_loss'),
            'r1': log.get('eval_rouge1'),
            'r2': log.get('eval_rouge2'),
            'rL': log.get('eval_rougeL')
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    # Tach biet log train (co loss) va log eval (co eval_loss)
    train_df = df.dropna(subset=['train_loss']).copy()
    eval_df = df.dropna(subset=['val_loss']).copy()
    return train_df, eval_df

def plot_results(vit5_paths, bart_paths):
    v_train, v_eval = parse_trainer_state(vit5_paths, "ViT5")
    b_train, b_eval = parse_trainer_state(bart_paths, "BARTpho")

    # 1. Ve bieu do Loss
    plt.figure(figsize=(10, 6))
    plt.plot(v_eval['epoch'], v_eval['val_loss'], label='ViT5 (Val Loss)', marker='o')
    plt.plot(b_eval['epoch'], b_eval['val_loss'], label='BARTpho (Val Loss)', marker='s')
    plt.title("Hội tụ Loss của hai mô hình")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True, linestyle='--')
    plt.savefig(f"{OUTPUT_DIR}/loss_comparison.png", dpi=300)

    # 2. Ve bieu do ROUGE-L (Do mach lac)
    plt.figure(figsize=(10, 6))
    plt.plot(v_eval['epoch'], v_eval['rL'], label='ViT5 (ROUGE-L)', marker='o', color='blue')
    plt.plot(b_eval['epoch'], b_eval['rL'], label='BARTpho (ROUGE-L)', marker='s', color='red')
    plt.title("Sự tăng trưởng chỉ số ROUGE-L qua các Epoch")
    plt.xlabel("Epoch")
    plt.ylabel("ROUGE-L Score")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{OUTPUT_DIR}/rougeL_growth.png", dpi=300)

    # 3. Luu bang so lieu cuoi cung ra CSV de ban insert vao Excel/Word
    final_stats = pd.concat([v_eval.tail(1), b_eval.tail(1)])
    final_stats.to_csv(f"{OUTPUT_DIR}/final_metrics_comparison.csv", index=False)
    print(f"Da trich xuat du lieu va ve bieu do vao: {OUTPUT_DIR}")

if __name__ == "__main__":
    plot_results(
        "results/models/vit5_summarization/checkpoint-7500/trainer_state.json",
        "results/models/bartpho_summarization/checkpoint-3750/trainer_state.json"
    )
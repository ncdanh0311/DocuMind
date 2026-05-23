import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

def plot_comparative_results():
    log_dir = "results/logs"
    fig_dir = "results/figures"
    os.makedirs(fig_dir, exist_ok=True)

    csv_files = glob.glob(os.path.join(log_dir, "*_history.csv"))
    if not csv_files:
        print("[ERROR] Khong tim thay file CSV nao de ve bieu do.")
        return

    plt.figure(figsize=(12, 6))
    
    # 1. Ve bieu do Val Loss so sanh cac model
    for file in csv_files:
        model_name = os.path.basename(file).replace("_history.csv", "")
        df = pd.read_csv(file)
        
        if 'val_loss' in df.columns:
            # Loai bo cac hang co val_loss bi NaN (log cua step, khong phai epoch)
            df_epoch = df.dropna(subset=['val_loss'])
            plt.plot(df_epoch['epoch'], df_epoch['val_loss'], marker='o', label=model_name)

    plt.title("So sanh Validation Loss giua cac Mo hinh")
    plt.xlabel("Epoch")
    plt.ylabel("Validation Loss")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    save_path = os.path.join(fig_dir, "comparative_val_loss.png")
    plt.savefig(save_path, dpi=300)
    print(f"[INFO] Da luu bieu do so sanh tai: {save_path}")

if __name__ == "__main__":
    plot_comparative_results()
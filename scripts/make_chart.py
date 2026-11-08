"""Draws images/late_delivery_causes.png (numbers come from sql/07_impact_estimate.sql)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

labels = ["Seller missed\nhandover deadline", "Carrier delay:\nRio + Northeast", "Carrier delay:\nrest of Brazil"]
orders = [9.0, 20.1, 70.8]
late = [27.8, 32.3, 39.9]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, ax = plt.subplots(figsize=(10, 4.6), dpi=200)
fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
y = np.arange(len(labels)); h = 0.36
b1 = ax.barh(y - h / 2 - 0.01, orders, h, color="#2a78d6", label="Share of all orders")
b2 = ax.barh(y + h / 2 + 0.01, late, h, color="#eb6834", label="Share of all LATE orders")
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_width() + 0.8, b.get_y() + b.get_height() / 2, f"{b.get_width():.0f}%", va="center",
                color="#0b0b0b", fontsize=10)
ax.set_yticks(y, labels, color="#0b0b0b"); ax.invert_yaxis()
ax.set_xlim(0, 80); ax.xaxis.set_visible(False)
for s in ["top", "right", "bottom"]:
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#bdbcb5")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, labelcolor="#52514e")
fig.suptitle("2 fixable causes = 29% of orders but 60% of late deliveries", x=0.02, y=0.97, ha="left",
             fontsize=15, fontweight="bold", color="#0b0b0b")
fig.text(0.02, 0.885, "Olist marketplace, Brazil · 96,469 delivered orders, 2016–2018 · real data",
         ha="left", fontsize=10, color="#52514e")
plt.tight_layout(rect=(0, 0, 1, 0.87))
plt.savefig("images/late_delivery_causes.png", facecolor=fig.get_facecolor())

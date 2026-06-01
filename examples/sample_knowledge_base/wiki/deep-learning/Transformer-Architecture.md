---
title: "Transformer Architecture Overview"
type: concept
created: 2026-05-31
tags:
  - deep-learning
  - transformer
  - attention
seed_type: REFINED
created_by: system
strength: 0.6351
last_activated: 2026-05-31
activation_count: 5
half_life: 30
---

# Transformer Architecture Overview

The Transformer is a neural network architecture introduced in "Attention Is All You Need" (Vaswani et al., 2017). It relies entirely on self-attention mechanisms, dispensing with recurrence and convolutions.

## Key Innovation: Self-Attention

Self-attention allows each position in a sequence to attend to all other positions, computing a weighted sum of their representations. This enables the model to capture long-range dependencies directly.

## Core Components

| Component | Function |
|:--|:--|
| Multi-Head Attention | Runs multiple attention operations in parallel |
| Positional Encoding | Adds information about token position in sequence |
| Feed-Forward Network | Processes each position independently |
| Layer Normalization | Stabilizes training |
| Residual Connections | Helps gradient flow in deep networks |

## Advantages

- **Parallelizable**: Unlike RNNs, all positions can be computed simultaneously
- **Long-range dependencies**: Direct attention between any two positions
- **Scalable**: Can be scaled up to billions of parameters

## See Also
- [[What-is-Machine-Learning]]
- Attention Is All You Need (Vaswani et al., 2017)

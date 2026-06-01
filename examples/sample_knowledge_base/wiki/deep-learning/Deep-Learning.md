---
title: "Deep Learning"
type: concept
created: 2026-05-31
tags:
  - deep-learning
  - neural-networks
  - AI
seed_type: REFINED
created_by: system
strength: 0.5178
last_activated: 2026-05-31
activation_count: 1
half_life: 30
---

# Deep Learning

Deep Learning is a subset of machine learning that uses neural networks with multiple layers (hence "deep") to learn hierarchical representations of data. Each layer transforms the data into increasingly abstract representations.

## Key Idea

Instead of hand-crafting features, deep learning learns feature representations automatically through successive transformations. A network with enough layers can approximate any function.

## Core Architectures

| Architecture | Key Innovation | Best For |
|:--|:--|:--|
| CNN (Convolutional) | Local receptive fields, weight sharing | Images, spatial data |
| RNN / LSTM | Sequential memory gates | Time series, text |
| Transformer | Self-attention mechanism | Language, multi-modal |

## Why Depth Matters

- **Shallow networks**: Limited representational power
- **Deep networks**: Each layer composes features from the previous layer
- **Tradeoff**: More depth = more power but harder to train (vanishing gradients, etc.)

## See Also
- [[What-is-Machine-Learning]]
- [[Transformer-Architecture]]
- [[Neural-Networks]]

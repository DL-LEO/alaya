---
title: "Neural Networks"
type: concept
created: 2026-05-31
tags:
  - neural-networks
  - deep-learning
  - fundamentals
seed_type: REFINED
created_by: system
strength: 0.52
last_activated: 2026-06-01
activation_count: 1
half_life: 30
---

# Neural Networks

A Neural Network is a computational model loosely inspired by biological neurons. It consists of layers of interconnected nodes that transform input signals through weighted connections and nonlinear activation functions.

## Basic Structure

```
Input Layer → Hidden Layer(s) → Output Layer

Each connection has a weight (w) and each node applies:
  output = activation_function(w * input + bias)
```

## Key Components

| Component | Role |
|:--|:--|
| Weights | Learnable parameters that scale signals |
| Bias | Learnable offset for each neuron |
| Activation Function | Introduces nonlinearity (ReLU, sigmoid, tanh) |
| Loss Function | Measures prediction error |
| Backpropagation | Computes gradients for weight updates |
| Optimizer | Updates weights to minimize loss (SGD, Adam) |

## Universal Approximation Theorem

A neural network with a single hidden layer and enough neurons can approximate any continuous function. In practice, depth (more layers) is more efficient than width (more neurons per layer).

## See Also
- [[What-is-Machine-Learning]]
- [[Deep-Learning]]
- [[Transformer-Architecture]]

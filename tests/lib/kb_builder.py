"""Knowledge-base builder — creates realistic wiki content for testing.

Constructs Alaya-compatible category directories, knowledge cards with
full YAML frontmatter, and runs build_index.py / perfume.py scripts inside
an isolated test workdir.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date

from lib.time_machine import today_str, set_strength, get_strength

# ---------------------------------------------------------------------------
# Card content templates keyed by broader topics
# ---------------------------------------------------------------------------

CARD_TEMPLATES: dict[str, tuple[list[str], str]] = {
    "deep-learning": (
        ["deep-learning", "neural-networks"],
        """# {title}

{title} is a foundational concept in deep learning.

## Key Points
- Core principle: {principle}
- Why it matters: {why}
- Common applications include {apps}.

## Relationship to Other Concepts
This connects closely with representation learning and end-to-end training.
""",
    ),
    "transformer": (
        ["deep-learning", "transformer", "attention", "nlp"],
        """# Transformer Architecture

The Transformer architecture was introduced in "Attention is All You Need" (Vaswani et al., 2017).

## Core Components
- Self-attention mechanism
- Multi-head attention
- Positional encoding
- Feed-forward layers

## Why It Matters
Transformers replaced RNNs as the dominant sequence model, enabling parallel training and longer-range dependencies.
""",
    ),
    "attention": (
        ["deep-learning", "attention", "transformer"],
        """# Attention Mechanism

Attention allows a model to focus on relevant parts of the input when producing each output element.

## Types
- **Self-attention**: attending within the same sequence
- **Cross-attention**: attending between encoder and decoder
- **Multi-head**: multiple parallel attention views

## Formula
Attention(Q,K,V) = softmax(QK^T/√d_k)V
""",
    ),
    "cnn": (
        ["deep-learning", "cnn", "vision"],
        """# Convolutional Neural Network

CNNs use convolutional filters to process grid-structured data like images.

## Key Ideas
- Local connectivity via kernels
- Parameter sharing across spatial locations
- Hierarchical feature learning (edges → shapes → objects)
""",
    ),
    "rl": (
        ["machine-learning", "reinforcement-learning", "agent"],
        """# Reinforcement Learning

RL trains an agent to make sequential decisions by maximizing cumulative reward.

## Components
- State, Action, Reward
- Policy (π): maps states to actions
- Value function: expected future reward

## Key Algorithms
- DQN, Policy Gradient, PPO, SAC
""",
    ),
    "yogacara": (
        ["philosophy", "yogacara", "buddhism", "consciousness"],
        """# 唯识学 (Yogacara)

瑜伽行派是佛教大乘两大派别之一，主张"万法唯识"。

## 核心概念
- **八识**: 前五识 + 第六意识 + 末那识 + 阿赖耶识
- **种子**: 阿赖耶识中储存的潜在功能
- **熏习**: 经验熏染种子，种子决定认知

## 与AI的类比
阿赖耶识 → 共享知识库 / 基础模型
末那识 → 角色/视角的执取
第六意识 → 推理过程
""",
    ),
    "transformer-yoga": (
        ["deep-learning", "transformer", "philosophy", "analogy"],
        """# Transformer 与唯识学的类比

Transformer 架构中的多层注意力与唯识八识有深刻的对应关系。

## 对应关系
- 自注意力 → 第六意识的"思量"功能
- 多头注意力 → 不同视角对同一数据的多重解读
- 位置编码 → 时间序列中的因果连续性

## 启发
这种跨领域映射为理解深度学习提供了全新的哲学视角。
""",
    ),
    "overfitting": (
        ["machine-learning", "generalization", "regularization"],
        """# Overfitting (过拟合)

Overfitting occurs when a model learns training data too well, including noise, at the expense of generalization.

## Symptoms
- High training accuracy, low test accuracy
- Complex decision boundaries
- Sensitivity to small input variations

## Solutions
- Regularization (L1, L2, Dropout)
- More training data
- Early stopping
- Model simplification
""",
    ),
    "generalization": (
        ["machine-learning", "generalization", "theory"],
        """# Generalization (泛化能力)

Generalization measures how well a model performs on unseen data.

## Key Concepts
- **Bias-Variance Tradeoff**: underfitting vs. overfitting
- **PAC Learning**: probably approximately correct
- **Double Descent**: modern phenomenon in overparameterized models

## In Practice
Good generalization requires the right inductive bias, sufficient data, and appropriate regularization.
""",
    ),
    "simplicity": (
        ["philosophy", "science", "simplicity", "feynman"],
        """# Simplicity (简洁性)

"Nature uses only the longest threads to weave her patterns, so each small piece of her fabric reveals the organization of the entire tapestry." — Feynman

## Principle
The simplest explanation that fits all the data is usually the correct one (Occam's Razor).

## In Engineering
Simple designs are easier to debug, maintain, and reason about. Complexity should be justified by necessity, not elegance.
""",
    ),
    "beauty-in-math": (
        ["mathematics", "beauty", "aesthetics", "elegance"],
        """# Beauty in Mathematics

Mathematical beauty is found in simplicity, symmetry, and unexpected connections.

## Examples
- Euler's identity: e^(iπ) + 1 = 0
- Fractal geometry: infinite complexity from simple rules
- Information theory: entropy as a unifying concept

## Why It Matters
Beauty is a reliable guide to truth — elegant solutions often generalize better.
""",
    ),
    "warm-recall": (
        ["psychology", "memory", "persona", "design"],
        """# Warm Recall Protocol

Warm recall transforms structured data into character-voiced recognition.

## Design Principles
- **Never** quote JSON directly
- **Always** translate data into natural, persona-appropriate language
- **Match** recall style to persona type (topic-first vs. mood-first vs. pattern-first)
- **Respect** memory boundaries between personas
""",
    ),
    "bias-variance": (
        ["machine-learning", "statistics", "bias-variance", "tradeoff"],
        """# Bias-Variance Tradeoff

The bias-variance tradeoff describes the tension between underfitting and overfitting.

## Definitions
- **Bias**: error from overly simplistic assumptions
- **Variance**: error from sensitivity to training data fluctuations

## Balancing Act
More complex models → lower bias, higher variance
Simpler models → higher bias, lower variance

The goal is to find the sweet spot that minimizes total error.
""",
    ),
}

ELEMENTARY_TOPICS = [
    ("python-basics", ["programming", "python"], "Python Programming Basics"),
    ("data-structures", ["computer-science", "algorithms"], "Data Structures"),
    ("linear-regression", ["machine-learning", "statistics"], "Linear Regression"),
    ("decision-trees", ["machine-learning", "algorithms"], "Decision Trees"),
    ("svm", ["machine-learning", "algorithms"], "Support Vector Machines"),
    ("entropy", ["information-theory", "mathematics"], "Entropy & Information Theory"),
    ("backpropagation", ["deep-learning", "optimization"], "Backpropagation"),
    ("embedding", ["nlp", "representation-learning"], "Word Embeddings"),
    ("lstm", ["deep-learning", "rnn", "nlp"], "LSTM Networks"),
    ("gan", ["deep-learning", "generative"], "Generative Adversarial Networks"),
]


def _make_card_yaml(title: str, tags: list[str], strength: float, last_act: str, act_count: int = 0) -> str:
    tags_str = json.dumps(tags)
    return (
        f"title: \"{title}\"\n"
        f"seed_type: REFINED\n"
        f"created_by: system\n"
        f"strength: {strength:.4f}\n"
        f"last_activated: {last_act}\n"
        f"activation_count: {act_count}\n"
        f"half_life: 30\n"
        f"tags: {tags_str}\n"
    )


# ---------------------------------------------------------------------------
# KB Builder class
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """Manages creation and maintenance of a test knowledge base."""

    def __init__(self, workdir: str):
        self.workdir = workdir
        self.wiki_dir = os.path.join(workdir, "wiki")
        self.alaya_dir = os.path.join(workdir, "alaya")
        self._script_base = workdir  # scripts are at workdir/scripts/

    # ---- low-level helpers ------------------------------------------------

    def run_script(self, script_name: str, args: list[str] | None = None) -> subprocess.CompletedProcess:
        """Run an alaya script inside the workdir and return result."""
        if args is None:
            args = []
        script = os.path.join(self.script_dir, script_name)
        if not os.path.exists(script):
            raise FileNotFoundError(f"Script not found: {script}")
        cmd = [sys.executable, script] + args
        env = os.environ.copy()
        from lib.time_machine import today_str
        env["ALAYA_TODAY"] = today_str()
        return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', cwd=self.workdir, env=env)

    @property
    def script_dir(self):
        return os.path.join(self.workdir, "scripts")

    # ---- category & card creation -----------------------------------------

    def add_category(self, cat_slug: str, description: str = "", card_names: list[str] | None = None) -> str:
        """Create category dir + _category.md. Returns slug."""
        cat_path = os.path.join(self.wiki_dir, cat_slug)
        os.makedirs(cat_path, exist_ok=True)
        cat_md = os.path.join(cat_path, "_category.md")
        links = "\n".join(f"- [[{n}]]" for n in (card_names or []))
        content = (
            f"---\ncategory: \"{cat_slug}\"\ndescription: \"{description}\"\n---\n\n"
            f"<!-- AUTO -->\n{links}\n<!-- END-AUTO -->\n"
        )
        with open(cat_md, "w", encoding="utf-8") as f:
            f.write(content)
        return cat_slug

    def add_card(self, cat_slug: str, name: str, content: str = "",
                 tags: list[str] | None = None, strength: float = 0.5,
                 last_activated: str | None = None) -> str:
        """Create a single knowledge card. Returns full path."""
        cat_path = os.path.join(self.wiki_dir, cat_slug)
        os.makedirs(cat_path, exist_ok=True)
        ts = last_activated or today_str()
        tags_str = json.dumps(tags or [])
        header = (
            f"---\ntitle: \"{name}\"\n"
            f"seed_type: REFINED\ncreated_by: system\n"
            f"strength: {strength:.4f}\n"
            f"last_activated: {ts}\n"
            f"activation_count: 0\nhalf_life: 30\n"
            f"tags: {tags_str}\n---\n\n"
        )
        body = content or f"# {name}\n\nAuto-generated test card for {cat_slug}.\n"
        fpath = os.path.join(cat_path, f"{name}.md")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(header + body)
        return fpath

    def add_template_card(self, cat_slug: str, template_key: str, name_override: str | None = None) -> str:
        """Create a card from the built-in content templates."""
        if template_key not in CARD_TEMPLATES:
            raise KeyError(f"Unknown template: {template_key}, available: {list(CARD_TEMPLATES.keys())}")
        tags, template = CARD_TEMPLATES[template_key]
        # Use name_override or generate from template_key (keep hyphens for filename compatibility)
        title = name_override or template_key.replace("-", " ").title()
        card_name = name_override or template_key  # use hyphens for filenames
        body = template.format(title=title, principle="learned representations",
                               why="it enables hierarchical feature extraction",
                               apps="classification, detection, generation")
        return self.add_card(cat_slug, card_name, body, tags=tags)

    def add_elementary_cards(self, cat_slug: str = "ml-fundamentals") -> list[str]:
        """Add a batch of elementary topic cards. Returns paths."""
        self.add_category(cat_slug, "Machine learning fundamentals")
        paths = []
        for slug, tags, title in ELEMENTARY_TOPICS:
            p = self.add_card(cat_slug, slug, f"# {title}\n\nContent about {title}.\n",
                              tags=tags, strength=0.5)
            paths.append(p)
        return paths

    # ---- script wrappers --------------------------------------------------

    def build_index(self, incremental: bool = False, category: str | None = None) -> subprocess.CompletedProcess:
        args = []
        if incremental:
            args.append("--incremental")
        if category:
            args.extend(["--category", category])
        args.extend([self.wiki_dir, self.alaya_dir])
        return self.run_script("build_index.py", args)

    def run_perfume_level1(self, cards: list[str], persona: str, topic: str = "",
                           turns: int = 3, tags: str = "", mood: str = "好奇") -> subprocess.CompletedProcess:
        args = ["--level", "1", "--cards", ",".join(cards), "--persona", persona,
                "--topic", topic, "--turns", str(turns), "--alaya", self.alaya_dir, "--wiki", self.wiki_dir]
        if tags:
            args.extend(["--tags", tags])
        if mood:
            args.extend(["--mood", mood])
        return self.run_script("perfume.py", args)

    def run_perfume_level2(self) -> subprocess.CompletedProcess:
        return self.run_script("perfume.py", ["--level", "2", "--alaya", self.alaya_dir, "--wiki", self.wiki_dir])

    def run_perfume_level3(self) -> subprocess.CompletedProcess:
        return self.run_script("perfume.py", ["--level", "3", "--alaya", self.alaya_dir, "--wiki", self.wiki_dir])

    def health_check(self) -> subprocess.CompletedProcess:
        return self.run_script("health_check.py", [self.wiki_dir, self.alaya_dir])

    def bi_observer(self) -> subprocess.CompletedProcess:
        return self.run_script("bi_observer.py", [self.alaya_dir])

    def batch_import(self, source_dir: str, category: str | None = None) -> subprocess.CompletedProcess:
        args = [source_dir]
        if category:
            args.extend(["--category", category])
        args.extend(["--wiki", self.wiki_dir, "--alaya", self.alaya_dir])
        return self.run_script("batch_import.py", args)

    # ---- card queries -----------------------------------------------------

    def card_path(self, cat: str, name: str) -> str:
        return os.path.join(self.wiki_dir, cat, f"{name}.md")

    def all_cards(self) -> list[tuple[str, str, str]]:
        """Return [(category, card_name, fpath)] for all cards."""
        result = []
        skip = {"_category.md", "index.md", "log.md"}
        if not os.path.isdir(self.wiki_dir):
            return result
        for cat in sorted(os.listdir(self.wiki_dir)):
            cat_path = os.path.join(self.wiki_dir, cat)
            if not os.path.isdir(cat_path):
                continue
            for fn in sorted(os.listdir(cat_path)):
                if fn.endswith(".md") and fn not in skip:
                    result.append((cat, fn[:-3], os.path.join(cat_path, fn)))
        return result

    def card_count(self) -> int:
        return len(self.all_cards())

    def category_names(self) -> list[str]:
        if not os.path.isdir(self.wiki_dir):
            return []
        return [d for d in sorted(os.listdir(self.wiki_dir))
                if os.path.isdir(os.path.join(self.wiki_dir, d))]

# draw_the_picture  
残差驱动直线线稿生成实验

---

## Overview / 概要

**EN**  
**draw_the_picture** is an experimental desktop application that converts an input
image into a line sketch composed of **pure black straight lines on a transparent
background**, using a residual-driven reconstruction approach.

This project is an **early-stage exploratory work** with no specific practical
application at this time.  
Its design and algorithmic ideas are inspired by and reference
*forza-painter*.

**日本語**  
**draw_the_picture** は、入力画像を  
**透明背景＋黒い直線のみ**で構成された線画へ変換する  
実験的なデスクトップアプリケーションです。

本プロジェクトは**明確な実用目的を持たない初期段階の試作**であり、  
設計思想および手法は *forza-painter* に着想を得ています。

---

## Features / 特徴

**EN**
- Straight lines only (no curves, no shading)
- Transparent background PNG export
- Iterative, observable drawing process
- User-controllable speed, line count, and line width
- No GPU or deep learning dependency

**日本語**
- 描画プリミティブは直線のみ
- 透明背景の PNG を出力
- 描画過程を逐次観察可能
- 線数・線幅・描画速度を調整可能
- GPU や深層学習モデルは不要

---

## Input & Output / 入出力

**Input**
- Formats: JPG / PNG / JPEG
- Import via file dialog or drag & drop

**Output**
- Format: PNG
- Transparent background
- Pure black lines only
- Output size matches the original image

---

## Algorithm / アルゴリズム概要

**EN**  
The core algorithm follows a **Residual-driven Reconstruction** strategy inspired by
*forza-painter*.

At each iteration:
1. A point is selected from the residual image
2. Multiple straight-line directions are evaluated
3. The line that explains the most residual pixels is chosen
4. The line is drawn and the residual is updated

**日本語**  
本プロジェクトは *forza-painter* の思想を参考にした  
**残差駆動型再構成アルゴリズム**を採用しています。

各反復処理において：
1. 未説明領域（Residual）から点を選択
2. 複数方向の直線を評価
3. 最も構造を説明する直線を選択
4. 描画後、Residual を更新

---

## Preprocessing / 前処理

- RGB → Grayscale
- Gaussian Blur
- Adaptive Threshold (binary)

Presets:
- Portrait（人物）
- Architecture（建築）
- Landscape（風景）

---

## Runtime Environment / 実行環境

- Python 3.9+
- macOS / Windows / Linux
- No GPU required

---

## Dependencies / 依存関係

```txt
numpy
opencv-python
PySide6

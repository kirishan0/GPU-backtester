# プロジェクト概要

簡易的な為替バックテスト環境です。CPU版とGPUモックを備えています。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CPUテスターの実行例

```bash
python -m project.engine.cpu_tester --config config.yaml --run-id TEST_RUN
```

## GPUモック実行例

```bash
python -m project.engine.gpu_proxy --config config.yaml --gpu-debug --run-id GPUDBG_001
```

## 実GPUの実行

```bash
python -m project.engine.gpu_proxy --config config.yaml --run-id GPUTASK_001
```

## ログと出力

- `logs/` に実行ログ
- `outputs/` にテスト結果やメタデータ
- GPUモックは `outputs/GPU/` 以下にRunごとの成果物を生成

## 片付け

```bash
rm -rf .venv outputs logs
```

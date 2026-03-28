# PowerForcaster

気象データと消費電力の関係性を調べるためのプロジェクト骨組み。

セットアップ:

```bash
# 仮想環境作成
python -m venv venv

# 有効化（Mac/Linux）
source venv/bin/activate

# ライブラリインストール
pip install -r requirements.txt
```

ディレクトリ構成（抜粋）:

```
data/
notebooks/
src/
main.py
requirements.txt
README.md
```

使い方:
- `main.py` を実行してパイプラインの雛形を動かせます（データ取得・前処理は各モジュールを実装してください）。

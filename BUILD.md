# ビルドガイド

Godius Crystal Buff Timer をソースコードから実行する方法と、Windows 用 EXE を作成する方法です。

## 必要なもの

- Windows 10 / 11
- Python 3.11 以降
- Git

Python をインストールする時は、`Add python.exe to PATH` を有効にしてください。

## ソースから実行する

リポジトリのルートで次を実行します。

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python source\godius_buff_timer.py
```

簡易起動用として、次のバッチファイルも利用できます。

```bat
source\run_buff_timer.bat
```

## EXE を作成する

次のコマンドを実行します。

```bat
scripts\build_exe.bat
```

成功すると、次のファイルが作成されます。

```text
dist\GodiusCrystalBuffTimer.exe
```

配布時は `dist\GodiusCrystalBuffTimer.exe` を GitHub Releases に添付してください。

## 手動でビルドする場合

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --clean GodiusCrystalBuffTimer.spec
```

## EXE 版の設定について

EXE には初期設定とアイコン画像が同梱されます。
起動後に検出位置やタイマー位置を調整すると、EXE と同じフォルダの `config.json` に保存されます。

設定を初期化したい場合は、EXE と同じフォルダに作成された `config.json` を削除してください。

## リリース前チェック

1. `dist\GodiusCrystalBuffTimer.exe` を起動できること
2. `F10` で赤い検出枠が表示されること
3. `Ctrl + 左ドラッグ` で検出枠を移動できること
4. Ice Crystal / Fire Crystal のバフアイコン検出で対応するタイマーが開始すること
5. 同じバフの再検出でタイマーが 598 秒前後に戻らないこと

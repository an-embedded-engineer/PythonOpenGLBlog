# GitHub Copilotと作る Pythonで OpenGL 3Dプログラミング

## 第1回「開発環境を整えよう」

[:contents]

### はじめに

前回は、このシリーズの概要とGitHub Copilotを活用した開発スタイルについて紹介しました。

今回から、実際の開発に入っていきます。まずは、Pythonで3Dプログラミングを行うための開発環境を構築しましょう。

### 必要なもの

このシリーズを進めるにあたって、以下のものが必要です：

- **Python 3.10以上**: 型ヒントなどの新しい機能を使用します
- **VS Code**: 開発エディタとして使用（GitHub Copilotとの連携に最適）
- **GitHub Copilot**: AIコーディング支援（有料サブスクリプションが必要）

### 開発環境の構築

#### 1. プロジェクトディレクトリの作成

まず、プロジェクト用のディレクトリを作成します。

```bash
mkdir PythonOpenGL
cd PythonOpenGL
```

#### 2. Python仮想環境の作成

プロジェクト専用のPython仮想環境を作成します。これにより、他のプロジェクトとパッケージのバージョンが競合することを防げます。

```bash
# 仮想環境の作成
python3 -m venv .venv

# 仮想環境の有効化（macOS/Linux）
source .venv/bin/activate

# 仮想環境の有効化（Windows）
# .venv\Scripts\activate
```

仮想環境が有効になると、ターミナルのプロンプトに`(.venv)`と表示されます。

#### 3. 必要なパッケージのインストール

3Dプログラミングに必要なパッケージをインストールします。

```bash
pip install glfw PyOpenGL numpy imgui-bundle
```

各パッケージの役割：

| パッケージ | 役割 |
|-----------|------|
| `glfw` | ウィンドウの作成、キーボード・マウス入力の処理 |
| `PyOpenGL` | OpenGLのPythonバインディング（3D描画API） |
| `numpy` | 数値計算ライブラリ（行列計算、頂点データ処理） |
| `imgui-bundle` | デバッグUI、パラメータ調整用のGUIライブラリ |

#### 4. インストールの確認

パッケージが正しくインストールされたか確認しましょう。

```bash
pip list | grep -E "glfw|PyOpenGL|numpy|imgui"
```

以下のような出力が表示されれば成功です（バージョンは異なる場合があります）：

```
glfw              2.10.0
imgui-bundle      1.92.5
numpy             2.3.5
PyOpenGL          3.1.10
```

### プロジェクト構成

今後、以下のようなディレクトリ構成でプロジェクトを進めていきます：

```
PythonOpenGL/
├── .venv/            # Python仮想環境（Gitには含めない）
├── src/
│   └── main.py       # メインプログラム
└── README.md         # プロジェクトの説明
```

#### srcディレクトリの作成

ソースコードを格納するディレクトリを作成します。

```bash
mkdir src
```

### 動作確認用のコード

環境が正しくセットアップされたか確認するため、簡単なテストコードを作成しましょう。

`src/main.py`を以下の内容で作成します：

```python
"""
PythonOpenGL - 環境構築確認用コード
"""
import sys


def check_packages() -> bool:
    """必要なパッケージがインストールされているか確認する"""
    packages = {
        'glfw': 'glfw',
        'OpenGL': 'PyOpenGL',
        'numpy': 'numpy',
        'imgui_bundle': 'imgui-bundle',
    }

    all_ok = True
    print("=== パッケージ確認 ===")

    for module_name, package_name in packages.items():
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {package_name}: {version}")
        except ImportError:
            print(f"✗ {package_name}: インストールされていません")
            all_ok = False

    return all_ok


def main() -> None:
    """メイン関数"""
    print("PythonOpenGL 環境構築確認\n")

    if check_packages():
        print("\n全てのパッケージが正しくインストールされています！")
        print("次回から、実際のOpenGLプログラミングを始めましょう。")
        sys.exit(0)
    else:
        print("\n一部のパッケージがインストールされていません。")
        print("pip install glfw PyOpenGL numpy imgui-bundle を実行してください。")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

### 動作確認

作成したコードを実行して、環境が正しくセットアップされているか確認します。

```bash
python src/main.py
```

以下のような出力が表示されれば、環境構築は完了です：

```
PythonOpenGL 環境構築確認

=== パッケージ確認 ===
✓ glfw: 2.10.0
✓ PyOpenGL: 3.1.10
✓ numpy: 2.3.5
✓ imgui-bundle: 1.92.5

全てのパッケージが正しくインストールされています！
次回から、実際のOpenGLプログラミングを始めましょう。
```

### VS Codeの設定（推奨）

VS Codeを使用している場合、以下の拡張機能をインストールすることをお勧めします：

- **Python**: Python言語サポート
- **Pylance**: 高速な型チェックとインテリセンス
- **GitHub Copilot**: AIコーディング支援

また、ワークスペースでPython仮想環境を認識させるため、VS Codeでプロジェクトフォルダを開いた後、コマンドパレット（Cmd+Shift+P / Ctrl+Shift+P）から「Python: Select Interpreter」を選択し、`.venv`内のPythonを選択してください。

### まとめ

今回は、Pythonで3Dプログラミングを行うための開発環境を構築しました。

- Python仮想環境の作成
- 必要なパッケージ（glfw, PyOpenGL, numpy, imgui-bundle）のインストール
- 動作確認用コードの実行

次回は、GLFWを使って実際にウィンドウを表示してみます。いよいよOpenGLプログラミングの第一歩です！

---

**前回**: [第0回「このシリーズについて」](https://an-embedded-engineer.hateblo.jp/entry/2025/11/29/232629)

**次回**: 第2回「GLFWでウィンドウを作る」（準備中）

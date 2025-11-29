
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

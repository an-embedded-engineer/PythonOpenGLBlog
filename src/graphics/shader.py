"""
シェーダー管理クラス

シェーダーのロード、コンパイル、リンク、使用を管理する
"""
from pathlib import Path

import OpenGL.GL as gl

from src.utils import logger


class ShaderCompileError(Exception):
    """シェーダーのコンパイルエラー"""
    pass


class ShaderLinkError(Exception):
    """シェーダープログラムのリンクエラー"""
    pass


class Shader:
    """
    シェーダープログラムを管理するクラス

    頂点シェーダーとフラグメントシェーダーをコンパイル・リンクし、
    GPUプログラムとして使用可能にする。
    """

    def __init__(self, vertex_path: str | Path, fragment_path: str | Path) -> None:
        """
        シェーダーファイルを読み込み、プログラムを作成する

        Args:
            vertex_path: 頂点シェーダーファイルのパス
            fragment_path: フラグメントシェーダーファイルのパス

        Raises:
            FileNotFoundError: シェーダーファイルが見つからない場合
            ShaderCompileError: シェーダーのコンパイルに失敗した場合
            ShaderLinkError: シェーダープログラムのリンクに失敗した場合
        """
        self._program_id: int = 0
        self._uniform_locations: dict[str, int] = {}

        # シェーダーソースの読み込み
        vertex_source = self._load_shader_source(vertex_path)
        fragment_source = self._load_shader_source(fragment_path)

        # シェーダーのコンパイル
        vertex_shader = self._compile_shader(vertex_source, gl.GL_VERTEX_SHADER, "vertex")
        fragment_shader = self._compile_shader(fragment_source, gl.GL_FRAGMENT_SHADER, "fragment")

        # シェーダープログラムのリンク
        self._program_id = self._link_program(vertex_shader, fragment_shader)

        # コンパイル済みシェーダーの削除（プログラムにリンク済みなので不要）
        gl.glDeleteShader(vertex_shader)
        gl.glDeleteShader(fragment_shader)

        logger.info(f"Shader program created: {Path(vertex_path).name}, {Path(fragment_path).name}")

    def _load_shader_source(self, path: str | Path) -> str:
        """
        シェーダーファイルを読み込む

        Args:
            path: シェーダーファイルのパス

        Returns:
            シェーダーソースコード

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Shader file not found: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()

        logger.debug(f"Loaded shader: {path}")
        return source

    def _compile_shader(self, source: str, shader_type: int, type_name: str) -> int:
        """
        シェーダーをコンパイルする

        Args:
            source: シェーダーソースコード
            shader_type: シェーダータイプ（gl.GL_VERTEX_SHADER or gl.GL_FRAGMENT_SHADER）
            type_name: ログ用のシェーダータイプ名

        Returns:
            コンパイル済みシェーダーID

        Raises:
            ShaderCompileError: コンパイルに失敗した場合
        """
        shader: int = gl.glCreateShader(shader_type)  # type: ignore[assignment]
        gl.glShaderSource(shader, source)
        gl.glCompileShader(shader)

        # コンパイル結果の確認
        success = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
        if success != gl.GL_TRUE:
            info_log = gl.glGetShaderInfoLog(shader).decode('utf-8')
            gl.glDeleteShader(shader)
            raise ShaderCompileError(f"{type_name} shader compile error:\n{info_log}")

        logger.debug(f"Compiled {type_name} shader successfully")
        return shader

    def _link_program(self, vertex_shader: int, fragment_shader: int) -> int:
        """
        シェーダープログラムをリンクする

        Args:
            vertex_shader: 頂点シェーダーID
            fragment_shader: フラグメントシェーダーID

        Returns:
            シェーダープログラムID

        Raises:
            ShaderLinkError: リンクに失敗した場合
        """
        program: int = gl.glCreateProgram()  # type: ignore[assignment]
        gl.glAttachShader(program, vertex_shader)
        gl.glAttachShader(program, fragment_shader)
        gl.glLinkProgram(program)

        # リンク結果の確認
        success = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)
        if success != gl.GL_TRUE:
            info_log = gl.glGetProgramInfoLog(program).decode('utf-8')
            gl.glDeleteProgram(program)
            raise ShaderLinkError(f"Shader program link error:\n{info_log}")

        logger.debug("Linked shader program successfully")
        return program

    def use(self) -> None:
        """このシェーダープログラムを使用する"""
        gl.glUseProgram(self._program_id)

    def delete(self) -> None:
        """シェーダープログラムを削除する"""
        if self._program_id:
            gl.glDeleteProgram(self._program_id)
            self._program_id = 0
            logger.debug("Shader program deleted")

    @property
    def program_id(self) -> int:
        """シェーダープログラムIDを取得"""
        return self._program_id

    # ===== Uniform変数設定メソッド =====

    def _get_uniform_location(self, name: str) -> int:
        """
        Uniform変数の位置を取得（キャッシュ付き）

        Args:
            name: Uniform変数名

        Returns:
            Uniform変数の位置（見つからない場合は-1）
        """
        if name not in self._uniform_locations:
            location = gl.glGetUniformLocation(self._program_id, name)
            self._uniform_locations[name] = location
            if location == -1:
                logger.warning(f"Uniform '{name}' not found in shader")
        return self._uniform_locations[name]

    def set_int(self, name: str, value: int) -> None:
        """整数のUniform変数を設定"""
        location = self._get_uniform_location(name)
        if location != -1:
            gl.glUniform1i(location, value)

    def set_float(self, name: str, value: float) -> None:
        """浮動小数点のUniform変数を設定"""
        location = self._get_uniform_location(name)
        if location != -1:
            gl.glUniform1f(location, value)

    def set_vec3(self, name: str, x: float, y: float, z: float) -> None:
        """3次元ベクトルのUniform変数を設定"""
        location = self._get_uniform_location(name)
        if location != -1:
            gl.glUniform3f(location, x, y, z)

    def set_vec4(self, name: str, x: float, y: float, z: float, w: float) -> None:
        """4次元ベクトルのUniform変数を設定"""
        location = self._get_uniform_location(name)
        if location != -1:
            gl.glUniform4f(location, x, y, z, w)

    def set_mat4(self, name: str, matrix) -> None:
        """4x4行列のUniform変数を設定（numpy配列を想定）"""
        location = self._get_uniform_location(name)
        if location != -1:
            gl.glUniformMatrix4fv(location, 1, gl.GL_FALSE, matrix)

    def __del__(self) -> None:
        """デストラクタ"""
        self.delete()

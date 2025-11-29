#version 330 core

// 頂点属性（入力）
layout (location = 0) in vec3 aPos;      // 頂点座標
layout (location = 1) in vec3 aColor;    // 頂点カラー

// フラグメントシェーダーへの出力
out vec3 vertexColor;

void main()
{
    // 頂点座標をクリップ座標に変換
    // 今回は変換なし（NDC座標をそのまま使用）
    gl_Position = vec4(aPos, 1.0);

    // 頂点カラーをフラグメントシェーダーに渡す
    vertexColor = aColor;
}

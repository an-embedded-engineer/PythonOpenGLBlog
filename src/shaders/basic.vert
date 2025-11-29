#version 330 core

// 頂点属性（入力）
layout (location = 0) in vec3 aPos;      // 頂点座標
layout (location = 1) in vec3 aColor;    // 頂点カラー

// Uniform変数
uniform mat4 model;      // Model行列
uniform mat4 view;       // View行列
uniform mat4 projection; // Projection行列

// フラグメントシェーダーへの出力
out vec3 vertexColor;

void main()
{
    // 頂点座標を変換
    // ローカル座標 → ワールド座標 → カメラ座標 → クリップ座標
    gl_Position = projection * view * model * vec4(aPos, 1.0);

    // 頂点カラーをフラグメントシェーダーに渡す
    vertexColor = aColor;
}

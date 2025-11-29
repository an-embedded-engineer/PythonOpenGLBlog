#version 330 core

// 頂点シェーダーからの入力
in vec3 vertexColor;

// 最終的なピクセルカラー（出力）
out vec4 FragColor;

void main()
{
    // 頂点カラーをそのまま出力（アルファは1.0で不透明）
    FragColor = vec4(vertexColor, 1.0);
}

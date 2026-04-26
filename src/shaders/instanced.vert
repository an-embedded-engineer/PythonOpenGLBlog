#version 330 core

// === 頂点属性（ベースジオメトリ、1頂点ごと） ===
layout (location = 0) in vec3 aPos;      // 頂点座標（ローカル空間）
layout (location = 1) in vec3 aColor;    // 頂点カラー（未使用、インスタンスカラーで上書き）

// === インスタンス属性（1インスタンスごと） ===
layout (location = 2) in vec3 aInstanceOffset;  // インスタンスの位置（ワールド空間）
layout (location = 3) in vec3 aInstanceColor;   // インスタンスのカラー
layout (location = 4) in float aInstanceScale;  // インスタンスのスケール

// Uniform変数（全インスタンス共通）
uniform mat4 model;       // グローバル変換行列（全体回転など）
uniform mat4 view;        // View行列
uniform mat4 projection;  // Projection行列

// フラグメントシェーダーへの出力
out vec3 vertexColor;

void main()
{
    // 1. ローカル座標にスケールを適用
    vec3 scaledPos = aPos * aInstanceScale;

    // 2. インスタンスのオフセット（位置）を加算 → ワールド座標
    vec3 worldPos = scaledPos + aInstanceOffset;

    // 3. グローバルmodel行列 → View行列 → Projection行列で変換
    gl_Position = projection * view * model * vec4(worldPos, 1.0);

    // インスタンスカラーを使用（頂点カラーの代わり）
    vertexColor = aInstanceColor;
}

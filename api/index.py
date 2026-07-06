import json
import os
import io
import math
import base64
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>像素小人生成机 · Chibi Maker</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root{
    --bg-deep:#0d0221;
    --panel:#170a3d;
    --panel-edge:#2c1866;
    --cyan:#00e5ff;
    --pink:#ff2e93;
    --yellow:#ffe156;
    --green:#3dff8a;
    --ink:#f2f0ff;
    --ink-dim:#9c8fd0;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{
    background:
      radial-gradient(circle at 20% 10%, #1c0f4a 0%, transparent 45%),
      radial-gradient(circle at 85% 90%, #2a0f4a 0%, transparent 40%),
      var(--bg-deep);
    color:var(--ink);
    font-family:'JetBrains Mono', monospace;
    min-height:100vh;
    padding:24px 16px 60px;
    display:flex;
    justify-content:center;
  }
  .cabinet{ width:100%; max-width:680px; }
  header{ text-align:center; margin-bottom:28px; }
  .eyebrow{
    font-family:'Press Start 2P', monospace;
    font-size:9px; letter-spacing:2px; color:var(--yellow);
    display:block; margin-bottom:14px;
  }
  h1{
    font-family:'Press Start 2P', monospace;
    font-size:clamp(15px, 4.5vw, 22px);
    line-height:1.6; margin:0 0 12px;
    text-shadow:3px 3px 0 var(--pink), 6px 6px 0 rgba(0,229,255,0.35);
  }
  header p{ color:var(--ink-dim); font-size:12.5px; max-width:480px; margin:0 auto; line-height:1.7; }

  .card{
    background:var(--panel);
    border:2px solid var(--panel-edge);
    border-radius:4px;
    padding:20px;
    margin-bottom:18px;
    box-shadow: 0 0 0 6px rgba(0,0,0,0.25) inset, 0 12px 30px rgba(0,0,0,0.4);
  }
  .card h2{
    font-family:'Press Start 2P', monospace;
    font-size:11px; color:var(--cyan); margin:0 0 14px; letter-spacing:1px;
  }

  .dropzone{
    border:2px dashed var(--panel-edge); border-radius:4px;
    padding:28px 16px; text-align:center; cursor:pointer;
    transition:border-color .15s, background .15s;
  }
  .dropzone:hover, .dropzone.drag{ border-color:var(--cyan); background:rgba(0,229,255,0.05); }
  .dropzone:focus-visible{ outline:3px solid var(--yellow); outline-offset:3px; }
  .dropzone span.icon{ font-size:26px; display:block; margin-bottom:8px; }
  .dropzone p{ margin:0; font-size:12px; color:var(--ink-dim); }
  #fileInput{ display:none; }
  .preview-row{ display:flex; align-items:center; gap:12px; margin-top:14px; }
  .preview-row img{ width:56px; height:56px; object-fit:cover; border-radius:4px; border:2px solid var(--panel-edge); }
  .preview-row span{ font-size:11.5px; color:var(--ink-dim); }

  button.pixel-btn{
    font-family:'Press Start 2P', monospace;
    font-size:10.5px; padding:13px 16px;
    border:2px solid var(--panel-edge); background:var(--panel); color:var(--ink);
    border-radius:4px; cursor:pointer; width:100%;
  }
  button.pixel-btn:hover{ border-color:var(--cyan); color:var(--cyan); }
  button.pixel-btn:focus-visible{ outline:3px solid var(--yellow); outline-offset:2px; }
  button.pixel-btn.primary{ background:var(--pink); border-color:var(--pink); color:#170a3d; }
  button.pixel-btn.primary:hover{ background:var(--yellow); border-color:var(--yellow); color:#170a3d; }
  button.pixel-btn:disabled{ opacity:.4; cursor:not-allowed; }

  .pose-grid{ display:grid; grid-template-columns:1fr; gap:14px; margin-top:16px; }
  @media (min-width:520px){ .pose-grid{ grid-template-columns:1fr 1fr; } }

  .pose-card{
    background:#0d0530; border:2px solid var(--panel-edge); border-radius:4px;
    padding:12px; display:flex; flex-direction:column; gap:10px;
  }
  .pose-card .pose-title{ font-size:11px; color:var(--yellow); text-align:center; }
  .stage{
    position:relative; border-radius:4px; overflow:hidden; background:#fff;
    aspect-ratio:1/1; display:flex; align-items:center; justify-content:center;
    border:2px solid var(--panel-edge);
  }
  .stage img{ width:100%; height:100%; object-fit:contain; image-rendering:pixelated; display:block; }
  .stage .status{ font-size:10.5px; color:#8a7fb0; text-align:center; padding:16px; }

  .pose-actions{ display:flex; gap:8px; }
  .pose-actions button, .pose-actions a{
    flex:1; font-size:9.5px; padding:9px 8px; text-align:center;
    text-decoration:none;
  }
  a.pixel-btn{ display:flex; align-items:center; justify-content:center; }

  .status-line{ font-size:11px; color:var(--ink-dim); margin-top:10px; min-height:16px; }
  .status-line.error{ color:var(--pink); }
  .status-line.ok{ color:var(--green); }

  footer{ text-align:center; font-size:10.5px; color:var(--ink-dim); margin-top:10px; line-height:1.8; }

  @media (prefers-reduced-motion: reduce){ * { animation:none !important; transition:none !important; } }
</style>
</head>
<body>
<div class="cabinet">
  <header>
    <span class="eyebrow">◆ UPLOAD · GENERATE · 4 POSES · SAVE GIF ◆</span>
    <h1>像素小人生成机</h1>
    <p>上传一张自己的照片，AI 会画出配色跟照片一致的 Q 版像素小人，自动生成比耶 / 跳跃 / 攻击 / 跑步四个姿势的循环 GIF。</p>
  </header>

  <div class="card">
    <h2>01 · 上传你的照片</h2>
    <div class="dropzone" id="dropzone" tabindex="0" role="button" aria-label="点击或拖拽上传照片">
      <span class="icon">▦</span>
      <p><b>点击选择</b> 或拖拽照片到这里<br>建议正脸 / 半身照，光线清晰</p>
    </div>
    <input type="file" id="fileInput" accept="image/*">
    <div class="preview-row" id="previewRow" style="display:none;">
      <img id="previewImg" alt="已上传照片预览">
      <span id="previewName"></span>
    </div>
  </div>

  <div class="card">
    <h2>02 · 生成四个姿势</h2>
    <button class="pixel-btn primary" id="generateBtn" disabled>▶ 生成全部姿势</button>
    <div class="status-line" id="globalStatus"></div>
    <div class="pose-grid" id="poseGrid"></div>
  </div>

  <footer>照片仅用于当次生成请求，不会被服务器保存 · 弹跳循环由服务端合成为 GIF</footer>
</div>

<script>
const POSES = [
  { id:'peace',  label:'比耶' },
  { id:'jump',   label:'跳跃' },
  { id:'attack', label:'站立攻击' },
  { id:'run',    label:'跑步' },
];

let uploadedImage = null;

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const previewRow = document.getElementById('previewRow');
const previewImg = document.getElementById('previewImg');
const previewName = document.getElementById('previewName');
const generateBtn = document.getElementById('generateBtn');
const globalStatus = document.getElementById('globalStatus');
const poseGrid = document.getElementById('poseGrid');

function buildPoseGrid(){
  poseGrid.innerHTML = '';
  POSES.forEach(pose => {
    const card = document.createElement('div');
    card.className = 'pose-card';
    card.innerHTML = `
      <div class="pose-title">${pose.label}</div>
      <div class="stage" id="stage-${pose.id}">
        <div class="status" id="status-${pose.id}">等待生成</div>
        <img id="img-${pose.id}" style="display:none;" alt="${pose.label} 像素小人 GIF">
      </div>
      <div class="pose-actions">
        <button class="pixel-btn" id="retry-${pose.id}" disabled>重新生成</button>
        <a class="pixel-btn" id="download-${pose.id}" style="pointer-events:none; opacity:.4;">下载 GIF</a>
      </div>
    `;
    poseGrid.appendChild(card);
  });
  POSES.forEach(pose => {
    document.getElementById(`retry-${pose.id}`).addEventListener('click', () => generatePose(pose));
  });
}
buildPoseGrid();

function loadFile(file){
  if(!file || !file.type.startsWith('image/')) return;
  const reader = new FileReader();
  reader.onload = e => {
    const dataUrl = e.target.result;
    const base64 = dataUrl.split(',')[1];
    uploadedImage = { mimeType: file.type, base64 };
    previewImg.src = dataUrl;
    previewName.textContent = file.name;
    previewRow.style.display = 'flex';
    generateBtn.disabled = false;
  };
  reader.readAsDataURL(file);
}

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('keydown', e => { if(e.key==='Enter'||e.key===' '){ e.preventDefault(); fileInput.click(); }});
fileInput.addEventListener('change', e => loadFile(e.target.files[0]));
['dragover','dragenter'].forEach(evt => dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.add('drag'); }));
['dragleave','drop'].forEach(evt => dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.remove('drag'); }));
dropzone.addEventListener('drop', e => loadFile(e.dataTransfer.files[0]));

generateBtn.addEventListener('click', async () => {
  if(!uploadedImage){ return; }
  generateBtn.disabled = true;
  globalStatus.className = 'status-line';
  for(const pose of POSES){
    globalStatus.textContent = `正在生成：${pose.label} ...`;
    await generatePose(pose);
  }
  globalStatus.textContent = '全部姿势处理完成';
  globalStatus.className = 'status-line ok';
  generateBtn.disabled = false;
});

async function generatePose(pose){
  const statusEl = document.getElementById(`status-${pose.id}`);
  const imgEl = document.getElementById(`img-${pose.id}`);
  const retryBtn = document.getElementById(`retry-${pose.id}`);
  const downloadLink = document.getElementById(`download-${pose.id}`);

  if(!uploadedImage){ statusEl.textContent = '请先上传照片'; return; }

  statusEl.style.display = 'block';
  statusEl.textContent = '生成中 ...';
  imgEl.style.display = 'none';
  retryBtn.disabled = true;
  downloadLink.style.pointerEvents = 'none';
  downloadLink.style.opacity = '.4';

  try{
    const res = await fetch('/api/generate', {
      method:'POST',
      headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({
        image_base64: uploadedImage.base64,
        mime_type: uploadedImage.mimeType,
        pose_id: pose.id,
      }),
    });
    const data = await res.json();
    if(!res.ok || data.error){ throw new Error(data.error || `请求失败 (${res.status})`); }

    const src = `data:image/gif;base64,${data.gif_base64}`;
    imgEl.src = src;
    imgEl.style.display = 'block';
    statusEl.style.display = 'none';

    downloadLink.href = src;
    downloadLink.download = `pixel-${pose.id}.gif`;
    downloadLink.style.pointerEvents = 'auto';
    downloadLink.style.opacity = '1';
    downloadLink.textContent = '下载 GIF';

    retryBtn.disabled = false;
  }catch(err){
    statusEl.style.display = 'block';
    statusEl.textContent = '出错了：' + err.message;
    retryBtn.disabled = false;
  }
}
</script>
</body>
</html>
'''

# ========== 豆包 API 配置（已更新为你的模型） ==========
ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
ARK_BASE_URL = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
# ✅ 已更新为你的模型：Seedream 5.0 Lite
MODEL = os.environ.get("ARK_MODEL", "doubao-seedream-5-0-260128")
ENDPOINT = f"{ARK_BASE_URL}/images/generations"

PROMPT_PREFIX = """Q版复古像素游戏风格的迷你角色，类似 Everskies / 复古 GBA 游戏角色的像素画风格，16-32 色限定色板，清晰的黑色像素描边，大头小身的 Q 版比例。

严格要求：
- 参考图中人物的发型、发色、肤色、瞳色、服装款式和颜色都要保留并贴近，不要换成其他颜色方案
- 背景必须是纯白色，不要任何阴影、地面、文字或装饰元素
- 画面里只有这一个完整角色，居中构图，全身可见
- 输出清晰的像素插画，不要照片写实风格

姿势要求："""

POSE_PROMPTS = {
    "peace": "角色保持微笑，抬起一只手在脸颊旁比出剪刀手/比耶手势，另一只手自然垂放，站立姿势，俏皮可爱的表情。",
    "jump": "角色呈现走路中途突然跳起的瞬间姿态，双脚离地，双臂向上或向外摆动增加动感，头发和衣摆因跳跃而飘起。",
    "attack": "角色摆出格斗游戏里站立出拳攻击的姿势，一只手向前用力打出，身体略微前倾，表情专注认真，动作干脆有力。",
    "run": "角色呈现侧面奔跑的动态姿势，双臂大幅摆动，一条腿向前跨出一条腿向后蹬，头发和衣角因奔跑向后飘动，速度感强烈。",
}


def call_seedream(image_b64, mime_type, pose_id):
    """调用豆包 Seedream 5.0 图生图 API"""
    prompt = PROMPT_PREFIX + POSE_PROMPTS[pose_id]
    
    # 构造 data URL（base64 图片）
    image_data_url = f"data:{mime_type};base64,{image_b64}"
    
    body = {
        "model": MODEL,
        "prompt": prompt,
        "image": image_data_url,      # 参考图（你的照片）
        "size": "1024x1024",          # 输出尺寸
        "response_format": "b64_json",  # 返回 base64 格式
        "watermark": False,           # 不加水印
    }
    
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ARK_API_KEY}",
        },
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise ValueError(f"豆包 API 返回 {e.code}: {detail[:500]}")
    
    # 解析返回的图片
    if data.get("data") and len(data["data"]) > 0:
        image_data = data["data"][0]
        if image_data.get("b64_json"):
            return image_data["b64_json"], "image/png"
        elif image_data.get("url"):
            # 如果返回的是 URL，就下载下来转成 base64
            try:
                with urllib.request.urlopen(image_data["url"], timeout=30) as img_resp:
                    img_bytes = img_resp.read()
                    return base64.b64encode(img_bytes).decode("utf-8"), "image/png"
            except Exception as e:
                raise ValueError(f"下载生成图片失败: {str(e)}")
    
    raise ValueError(f"模型没有返回图片，请检查 API Key 是否正确。返回内容：{json.dumps(data, ensure_ascii=False)[:300]}")


def make_bounce_gif(png_b64):
    from PIL import Image
    img_bytes = base64.b64decode(png_b64)
    im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

    size = 320
    target = int(size * 0.86)
    im.thumbnail((target, target))

    n_frames = 16
    frames = []
    for i in range(n_frames):
        t = (i / n_frames) * math.pi * 2 * 0.65
        bounce = int(math.sin(t) * 6)
        squash = 1 + math.sin(t) * 0.015

        w = max(1, int(im.width * squash))
        h = max(1, int(im.height * (2 - squash)))
        frame_img = im.resize((w, h))

        canvas = Image.new("RGB", (size, size), (255, 255, 255))
        x = (size - w) // 2
        y = (size - h) // 2 + bounce
        canvas.paste(frame_img, (x, y), frame_img)
        frames.append(canvas)

    buf = io.BytesIO()
    frames[0].save(
        buf, format="GIF", save_all=True, append_images=frames[1:],
        duration=55, loop=0, optimize=True,
    )
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@app.route("/", methods=["GET"])
def index():
    return Response(HTML_PAGE, mimetype="text/html")


@app.route("/api/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return ("", 204)
    try:
        payload = request.get_json(force=True, silent=True) or {}
        image_b64 = payload.get("image_base64")
        mime_type = payload.get("mime_type", "image/jpeg")
        pose_id = payload.get("pose_id")

        if not image_b64:
            raise ValueError("缺少 image_base64")
        if pose_id not in POSE_PROMPTS:
            raise ValueError("未知的 pose_id")
        if not ARK_API_KEY:
            raise ValueError("服务器未配置 ARK_API_KEY 环境变量")

        png_b64, _ = call_seedream(image_b64, mime_type, pose_id)
        gif_b64 = make_bounce_gif(png_b64)

        return jsonify({"gif_base64": gif_b64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========== Vercel 入口 ==========
handler = app.wsgi_app

from http.server import BaseHTTPRequestHandler
import json
import os
import io
import math
import base64
import urllib.request
import urllib.error
from PIL import Image

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
MODEL = "gemini-3.1-flash-image-preview"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPT_PREFIX = """请参考这张上传的人物照片，画一个 Q 版复古像素游戏风格的迷你角色（类似 Everskies / 复古 GBA 游戏角色的像素画风格，16-32 色限定色板，清晰的黑色像素描边，大头小身的 Q 版比例）。

严格要求：
- 角色的发型、发色、肤色、瞳色、服装款式和颜色都要参考并贴近这张照片里人物的实际配色，不要换成其他颜色方案（不要用复古绿、赛博霓虹等和原图无关的配色）。
- 背景必须是纯白色，不要任何阴影、地面、文字或装饰元素。
- 画面里只有这一个完整角色，居中构图，全身可见。
- 输出清晰的像素插画，不要照片写实风格。

姿势要求："""

POSE_PROMPTS = {
    "peace": "角色保持微笑，抬起一只手在脸颊旁比出剪刀手/比耶手势，另一只手自然垂放，站立姿势，俏皮可爱的表情。",
    "jump": "角色呈现走路中途突然跳起的瞬间姿态，双脚离地，双臂向上或向外摆动增加动感，头发和衣摆因跳跃而飘起。",
    "attack": "角色摆出格斗游戏里站立出拳攻击的姿势，一只手向前用力打出，身体略微前倾，表情专注认真，动作干脆有力。",
    "run": "角色呈现侧面奔跑的动态姿势，双臂大幅摆动，一条腿向前跨出一条腿向后蹬，头发和衣角因奔跑向后飘动，速度感强烈。",
}


def call_gemini(image_b64, mime_type, pose_id):
    prompt = PROMPT_PREFIX + POSE_PROMPTS[pose_id]
    body = {
        "contents": [{
            "parts": [
                {"inlineData": {"mimeType": mime_type, "data": image_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }
    req = urllib.request.Request(
        f"{ENDPOINT}?key={GOOGLE_API_KEY}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise ValueError(f"Gemini 接口返回 {e.code}: {detail[:200]}")

    parts = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [])
    )
    for p in parts:
        inline = p.get("inlineData")
        if inline and inline.get("data"):
            return inline["data"], inline.get("mimeType", "image/png")
    raise ValueError("模型没有返回图片，换个姿势或稍后重试")


def make_bounce_gif(png_b64):
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


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))

            image_b64 = payload.get("image_base64")
            mime_type = payload.get("mime_type", "image/jpeg")
            pose_id = payload.get("pose_id")

            if not image_b64:
                raise ValueError("缺少 image_base64")
            if pose_id not in POSE_PROMPTS:
                raise ValueError("未知的 pose_id")
            if not GOOGLE_API_KEY:
                raise ValueError("服务器未配置 GOOGLE_API_KEY 环境变量")

            png_b64, _ = call_gemini(image_b64, mime_type, pose_id)
            gif_b64 = make_bounce_gif(png_b64)

            self._send_json(200, {"gif_base64": gif_b64})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
        
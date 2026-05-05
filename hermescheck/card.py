"""Render hermescheck report cards as PNG images."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any

from hermescheck import __version__


class CardRenderError(RuntimeError):
    """Raised when a report card cannot be rendered."""


def _load_pillow() -> tuple[Any, Any, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
    except ImportError as exc:  # pragma: no cover - depends on optional package state
        raise CardRenderError(
            "Report card rendering requires Pillow. Install it with `pip install 'hermescheck[card]'`."
        ) from exc
    return Image, ImageDraw, ImageFilter, ImageFont


def render_report_card(
    results: dict[str, Any],
    output_path: str | Path,
    *,
    title: str | None = None,
    subtitle: str | None = None,
) -> Path:
    """Render a clean shareable PNG card from hermescheck JSON results."""

    Image, ImageDraw, ImageFilter, ImageFont = _load_pillow()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    width, height, scale = 1600, 1080, 2
    canvas = Image.new("RGBA", (width * scale, height * scale), "#eef2f3")
    draw = ImageDraw.Draw(canvas)

    def sc(value: float) -> int:
        return int(round(value * scale))

    def scaled_box(x0: float, y0: float, x1: float, y1: float) -> list[int]:
        return [sc(x0), sc(y0), sc(x1), sc(y1)]

    font_paths = {
        "sans": [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/Avenir Next.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/arial.ttf",
        ],
        "display": [
            "/System/Library/Fonts/Avenir Next.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ],
        "mono": [
            "/System/Library/Fonts/Menlo.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "C:/Windows/Fonts/consola.ttf",
        ],
        "number": [
            "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf",
            "/System/Library/Fonts/Avenir Next.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ],
    }

    def font(size: int, face: str = "sans") -> Any:
        for path in font_paths.get(face, []) + font_paths["sans"]:
            try:
                return ImageFont.truetype(path, sc(size), index=0)
            except OSError:
                continue
        return ImageFont.load_default()

    fonts = {
        "brand": font(46, "display"),
        "title": font(52),
        "section": font(30),
        "micro": font(19),
        "label": font(22),
        "body": font(26),
        "body_small": font(23),
        "score": font(126, "number"),
        "number_small": font(28, "number"),
        "mono": font(21, "mono"),
    }

    ink = "#142027"
    muted = "#66737c"
    paper = "#fbfcfa"
    green = "#1e7f5c"
    amber = "#c77a17"
    red = "#bd3b32"
    blue = "#315b8d"
    charcoal = "#20292f"
    blue_soft = "#dceaff"

    for x in range(0, width, 80):
        draw.line([sc(x), 0, sc(x), sc(height)], fill=(205, 216, 219, 70), width=sc(1))
    for y in range(0, height, 80):
        draw.line([0, sc(y), sc(width), sc(y)], fill=(205, 216, 219, 45), width=sc(1))
    for offset in range(-300, 1900, 180):
        draw.line([sc(offset), 0, sc(offset + 560), sc(height)], fill=(49, 91, 141, 20), width=sc(2))
    random.seed(30)
    for _ in range(9500):
        x = random.randrange(width * scale)
        y = random.randrange(height * scale)
        alpha = random.randrange(7, 20)
        draw.point(
            (x, y),
            fill=random.choice([(255, 255, 255, alpha), (20, 32, 39, alpha // 2), (49, 91, 141, alpha // 2)]),
        )

    def shadow_round(
        rect: tuple[float, float, float, float],
        radius: int,
        *,
        offset: tuple[int, int] = (0, 18),
        blur: int = 28,
        color: tuple[int, int, int, int] = (20, 32, 39, 38),
    ) -> None:
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow = ImageDraw.Draw(layer)
        x0, y0, x1, y1 = rect
        ox, oy = offset
        shadow.rounded_rectangle(scaled_box(x0 + ox, y0 + oy, x1 + ox, y1 + oy), radius=sc(radius), fill=color)
        canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(sc(blur))))

    def rounded_rect(
        rect: tuple[float, float, float, float], radius: int, fill: str, outline: str | None = None
    ) -> None:
        draw.rounded_rectangle(scaled_box(*rect), radius=sc(radius), fill=fill, outline=outline)

    def text(x: float, y: float, value: str, face: Any, fill: str = ink, anchor: str | None = None) -> None:
        draw.text((sc(x), sc(y)), value, font=face, fill=fill, anchor=anchor)

    def text_length(value: str, face: Any) -> float:
        return draw.textlength(value, font=face) / scale

    def wrap(value: str, face: Any, max_width: float) -> list[str]:
        tokens: list[str] = []
        buffer = ""
        for char in value:
            if char.isspace():
                if buffer:
                    tokens.append(buffer)
                    buffer = ""
                tokens.append(char)
            elif ord(char) < 128 and char not in "/:-_.":
                buffer += char
            else:
                if buffer:
                    tokens.append(buffer)
                    buffer = ""
                tokens.append(char)
        if buffer:
            tokens.append(buffer)

        lines: list[str] = []
        line = ""
        for token in tokens:
            candidate = line + token
            if text_length(candidate, face) <= max_width or not line:
                line = candidate
            else:
                lines.append(line.strip())
                line = token.strip()
        if line.strip():
            lines.append(line.strip())
        return lines

    def paragraph(
        x: float,
        y: float,
        value: str,
        face: Any,
        max_width: float,
        line_height: int,
        *,
        fill: str = muted,
        max_lines: int | None = None,
    ) -> None:
        lines = wrap(value, face, max_width)
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines]
            while lines[-1] and text_length(lines[-1] + "...", face) > max_width:
                lines[-1] = lines[-1][:-1]
            lines[-1] += "..."
        for index, line in enumerate(lines):
            text(x, y + index * line_height, line, face, fill)

    def chip(x: float, y: float, label: str, fill: str, foreground: str) -> float:
        chip_width = text_length(label, fonts["label"]) + 36
        rounded_rect((x, y, x + chip_width, y + 40), 20, fill)
        text(x + 18, y + 9, label, fonts["label"], foreground)
        return x + chip_width + 10

    verdict = results.get("executive_verdict", {})
    scope = results.get("scope", {})
    metadata = results.get("scan_metadata", {})
    summary = results.get("severity_summary", {})
    maturity = results.get("maturity_score", {})
    findings = results.get("findings", [])

    card_title = title or f"{scope.get('target_name') or 'Agent'} Architecture Audit"
    card_subtitle = (
        subtitle or verdict.get("primary_failure_mode") or maturity.get("share_line") or "Architecture health report"
    )
    urgent_fix = verdict.get("most_urgent_fix") or "No urgent fix was reported."
    score = int(maturity.get("score") or 0)
    era_name = str(maturity.get("era_name") or "Unknown era")
    version = f"v{metadata.get('hermescheck_version') or metadata.get('version') or __version__}"

    shadow_round((54, 48, 1546, 1018), 38, blur=32)
    rounded_rect((54, 48, 1546, 1018), 38, paper, "#e5eaed")
    rounded_rect((54, 48, 82, 1018), 38, charcoal)
    for yy, color in [(86, green), (170, blue), (254, amber), (338, red), (422, "#9aa7af")]:
        rounded_rect((62, yy, 74, yy + 54), 6, color)

    rounded_rect((118, 92, 178, 152), 16, ink)
    text(148, 111, "hc", font(25, "mono"), "#f7fbf8", anchor="ma")
    text(204, 86, "HermesCheck", fonts["brand"], ink)
    text(207, 137, "agent architecture audit card", fonts["micro"], muted)
    next_x = chip(1068, 96, version, "#edf7f2", green)
    next_x = chip(next_x, 96, "runtime scope", blue_soft, blue)
    chip(next_x, 96, "report card", "#f0f2f3", muted)

    text(118, 194, card_title, fonts["title"], ink)
    paragraph(120, 262, card_subtitle, fonts["body"], 760, 38, fill=charcoal, max_lines=2)
    text(120, 340, "Most urgent fix", fonts["label"], amber)
    paragraph(120, 374, urgent_fix, fonts["body_small"], 790, 34, max_lines=3)

    shadow_round((1010, 178, 1468, 568), 34, offset=(0, 14), blur=20, color=(20, 32, 39, 28))
    rounded_rect((1010, 178, 1468, 568), 34, "#f7faf8", "#dfe8e5")
    cx, cy, radius = 1239, 348, 146
    draw.arc(scaled_box(cx - radius, cy - radius, cx + radius, cy + radius), 130, 410, fill="#d8e1de", width=sc(22))
    draw.arc(
        scaled_box(cx - radius, cy - radius, cx + radius, cy + radius),
        130,
        130 + 280 * max(0, min(score, 100)) / 100,
        fill=red if score < 40 else amber if score < 70 else green,
        width=sc(22),
    )
    for index in range(11):
        angle = math.radians(130 + index * 28)
        x0 = cx + math.cos(angle) * (radius - 8)
        y0 = cy + math.sin(angle) * (radius - 8)
        x1 = cx + math.cos(angle) * (radius + 13)
        y1 = cy + math.sin(angle) * (radius + 13)
        draw.line([sc(x0), sc(y0), sc(x1), sc(y1)], fill=(160, 174, 176, 150), width=sc(2))
    text(cx, cy - 62, str(score), fonts["score"], ink, anchor="ma")
    text(cx + 92, cy - 46, "/100", fonts["number_small"], muted, anchor="la")
    text(cx, cy + 56, era_name, font(32), amber, anchor="ma")
    text(cx, cy + 96, "architecture era", fonts["micro"], muted, anchor="ma")

    severity_colors = {"critical": "#731f1b", "high": red, "medium": amber, "low": green}
    total = max(sum(int(summary.get(key, 0) or 0) for key in severity_colors), 1)
    bar_x = 1068
    for severity in ("critical", "high", "medium", "low"):
        amount = int(summary.get(severity, 0) or 0)
        segment_width = 342 * amount / total
        if segment_width > 0:
            rounded_rect((bar_x, 506, bar_x + segment_width, 524), 9, severity_colors[severity])
        bar_x += segment_width
    legend_x = 1064
    for label, severity in (("HIGH", "high"), ("MED", "medium"), ("LOW", "low")):
        rounded_rect((legend_x, 532, legend_x + 16, 548), 4, severity_colors[severity])
        text(legend_x + 24, 528, f"{label} {summary.get(severity, 0)}", fonts["micro"], muted)
        legend_x += 108

    text(120, 622, "Priority findings", fonts["section"], ink)
    for index, item in enumerate(findings[:4]):
        x = 120 + (index % 2) * 430
        y = 680 + (index // 2) * 116
        severity = str(item.get("severity", "low")).lower()
        accent = severity_colors.get(severity, muted)
        rounded_rect((x, y, x + 390, y + 88), 20, "#ffffff", "#e0e6e8")
        rounded_rect((x, y, x + 8, y + 88), 8, accent)
        text(x + 26, y + 18, severity.upper(), fonts["micro"], accent)
        paragraph(
            x + 26,
            y + 43,
            str(item.get("title", "Untitled finding")),
            fonts["body_small"],
            330,
            30,
            fill=ink,
            max_lines=1,
        )

    text(1010, 622, "Runtime signals", fonts["section"], ink)
    signals = maturity.get("signal_points", [])[:4]
    max_points = max([int(signal.get("points", 0) or 0) for signal in signals] + [1])
    for index, signal in enumerate(signals):
        y = 678 + index * 66
        points = int(signal.get("points", 0) or 0)
        label = str(signal.get("label") or signal.get("key") or "signal")
        text(1010, y, label, fonts["body_small"], ink)
        text(1436, y, str(points), fonts["number_small"], blue, anchor="ra")
        rounded_rect((1012, y + 34, 1438, y + 44), 5, "#e4eaee")
        rounded_rect((1012, y + 34, 1012 + 426 * points / max_points, y + 44), 5, blue)

    rounded_rect((116, 944, 1480, 1004), 20, ink)
    for separator in (430, 858, 1210):
        draw.line([sc(separator), sc(960), sc(separator), sc(988)], fill="#314047", width=sc(1))
    text(144, 958, "audit scope", fonts["micro"], "#b7c4c9")
    text(144, 980, "production runtime", fonts["micro"], "#f7fbf8")
    text(470, 958, "excluded noise", fonts["micro"], "#b7c4c9")
    text(470, 980, "tests / fixtures / deps", fonts["micro"], "#f7fbf8")
    text(898, 958, "card source", fonts["micro"], "#b7c4c9")
    text(898, 980, "Hermes audit · cognitive_runtime", fonts["micro"], "#f7fbf8")
    text(1248, 968, str(metadata.get("scan_timestamp", ""))[:10], fonts["label"], "#f7fbf8")

    text(118, 1034, "schema: cognitive_runtime", fonts["mono"], "#87949b")
    text(1320, 1034, "hermescheck card", fonts["mono"], "#87949b")

    final = canvas.resize((width, height), Image.Resampling.LANCZOS).convert("RGB")
    final.save(output, quality=96)
    return output

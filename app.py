import base64
import math
import threading
import time
from functools import lru_cache
from itertools import combinations

import cv2
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
APP_VERSION = "WEB+API-v1.1"

WEB_HTML = '<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>루미나의 회랑 루트 분석기</title><style>\n*{box-sizing:border-box}body{margin:0;background:#eef3f8;color:#182230;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif}.container{width:min(1250px,96%);margin:20px auto 45px}.notice{padding:10px 14px;background:#ffffffd1;border:1px solid #d8e0ea;border-radius:12px;color:#667085;font-size:13px;line-height:1.55}h1{margin:17px 0 5px;font-size:clamp(27px,4vw,43px);letter-spacing:-1.5px}.credit{font-size:.54em;font-weight:900;white-space:nowrap}.credit b{color:#5148e5}.description{color:#667085;line-height:1.7;margin-bottom:19px}.fast-card{background:white;border:2px solid #8177ef;border-radius:18px;padding:22px;margin-bottom:18px}.fast-title{font-size:21px;font-weight:900;margin-bottom:10px}.fast-flow{line-height:1.9;font-size:17px}.fast-flow strong{color:#5148e5}.connect-box{margin-top:15px;padding:14px;border-radius:11px;background:#f7f7ff}.code-row{display:flex;flex-wrap:wrap;align-items:center;gap:9px;margin-top:8px}.code{padding:9px 12px;border-radius:8px;background:white;border:1px solid #d8dce5;font-family:Consolas,monospace;font-size:17px;font-weight:900;letter-spacing:1px}.small-button{border:0;border-radius:8px;padding:9px 12px;background:#344054;color:white;cursor:pointer;font-weight:800}.download-button{display:inline-block;margin-top:14px;padding:12px 16px;border-radius:10px;background:#5148e5;color:white;text-decoration:none;font-weight:900}.download-button:hover{background:#4338ca}.upload-box{background:white;border:2px dashed #98a7b9;border-radius:18px;padding:38px 20px;text-align:center;cursor:pointer}.upload-box:hover,.upload-box.dragover{border-color:#5148e5;background:#f7f8ff}.upload-icon{font-size:42px}.upload-title{margin-top:9px;font-size:18px;font-weight:800}.upload-sub{margin-top:7px;color:#7b8794}#fileInput{display:none}.loading,.error-box{display:none;margin-top:17px;padding:15px;border-radius:10px;font-weight:800}.loading{background:#fff8df;color:#805b00}.error-box{background:#fff0f0;color:#b42318}.result{display:none;margin-top:28px}.result-grid{display:grid;grid-template-columns:minmax(300px,.8fr) minmax(400px,1.2fr);gap:24px}.card{background:white;border-radius:18px;padding:27px;box-shadow:0 4px 22px #0000000f}.best-card{border:2px solid #e4a600}.big-number{margin-top:20px;font-size:58px;font-weight:900;color:#5148e5}.info-label{margin-top:21px;font-weight:800}.info-value{margin-top:4px;font-size:18px}.same-count{margin-top:17px;padding:11px 13px;border-radius:9px;background:#f5f3ff;color:#4c3eb6;font-weight:800}.start-card{margin-top:18px}.start-row{display:flex;justify-content:space-between;padding:13px 9px;border-bottom:1px solid #e7e9ef}.start-row.best{background:#fff6d3;border-radius:8px;font-weight:800}.route-tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}.route-tab{border:1px solid #d7dce5;background:#f8f9fb;padding:9px 12px;border-radius:9px;cursor:pointer;font-weight:800}.route-tab.active{color:white;background:#5148e5;border-color:#5148e5}.route-meta{color:#667085;margin-bottom:12px}.route-image{width:100%;max-height:850px;object-fit:contain;border-radius:10px}.live{display:inline-block;margin-left:8px;padding:5px 8px;border-radius:999px;background:#e8f7ee;color:#087a3e;font-size:12px;font-weight:900}@media(max-width:800px){.result-grid{grid-template-columns:1fr}}\n</style></head><body><div class="container"><div class="notice">비공식 팬 제작 도구 · 본 프로그램은 게임사 및 공식 서비스와 제휴·승인·후원 관계가 없는 독립적인 보조 분석 프로그램입니다. 게임명·이미지·상표 등 각 권리는 해당 권리자에게 있습니다.</div><h1>🎯 루미나의 회랑 루트 분석기 <span class="credit">(Made by <b>말짧</b>)</span></h1><div class="description">점선 배치를 분석해 1단계부터 10단계까지 방문 가능한 최대 방 수와 동일 최대 루트를 계산합니다.</div><div class="fast-card"><div class="fast-title">⚡ F8 헬퍼 사용법 <span class="live">웹 연동</span></div><div class="fast-flow">1. 아래 <strong>내 연결 코드</strong>를 F8 헬퍼에 한 번 입력<br>2. 헬퍼에서 게임판 영역을 한 번 지정<br>3. 이후 게임에서 <strong>리롤 → F8</strong><br>4. 이 페이지가 자동으로 새 결과를 표시</div><div class="connect-box"><b>내 연결 코드</b><div class="code-row"><span id="clientCode" class="code"></span><button class="small-button" onclick="copyCode()">코드 복사</button><button class="small-button" onclick="newCode()">새 코드 만들기</button></div></div><a class="download-button" href="https://github.com/TW-MZZ/lumina-route-api/releases/download/v1.0/Lumina-F8-Helper-v1.0.zip">⚡ F8 헬퍼 다운로드</a><div style="margin-top:13px;color:#667085;line-height:1.7">헬퍼 없이도 <b>Win + Shift + S → Ctrl + V</b>로 바로 분석할 수 있습니다.</div></div><div id="uploadBox" class="upload-box"><div class="upload-icon">📷</div><div class="upload-title">이미지 드래그 / 클릭</div><div class="upload-sub">또는 캡처 후 Ctrl + V</div></div><input id="fileInput" type="file" accept="image/png,image/jpeg,image/jpg"><div id="loading" class="loading">이미지를 분석하고 있습니다...</div><div id="errorBox" class="error-box"></div><div id="result" class="result"><div class="result-grid"><div><div class="card best-card"><h2>🏆 최적 결과</h2><div id="bestCount" class="big-number">0방</div><div class="info-label">추천 시작 방</div><div id="bestStart" class="info-value">-</div><div class="info-label">최종 도착</div><div id="finalRoom" class="info-value">-</div><div id="sameCount" class="same-count"></div></div><div class="card start-card"><h2>📊 시작 방별 결과</h2><div id="starts"></div></div></div><div class="card"><h2>🗺️ 최적 루트</h2><div id="routeTabs" class="route-tabs"></div><div id="routeMeta" class="route-meta"></div><img id="routeImage" class="route-image"></div></div></div></div><script>\nconst uploadBox=document.getElementById(\'uploadBox\'),fileInput=document.getElementById(\'fileInput\'),loading=document.getElementById(\'loading\'),errorBox=document.getElementById(\'errorBox\');let currentResult=null,currentRevision=0;function randomCode(){const a=\'ABCDEFGHJKLMNPQRSTUVWXYZ23456789\';let r=\'\';for(let i=0;i<10;i++)r+=a[Math.floor(Math.random()*a.length)];return r}function getClientCode(){let c=localStorage.getItem(\'luminaClientCode\');if(!c){c=randomCode();localStorage.setItem(\'luminaClientCode\',c)}return c}function refreshCodeUI(){document.getElementById(\'clientCode\').textContent=getClientCode()}function copyCode(){navigator.clipboard.writeText(getClientCode())}function newCode(){localStorage.setItem(\'luminaClientCode\',randomCode());currentRevision=0;refreshCodeUI()}refreshCodeUI();uploadBox.onclick=()=>fileInput.click();uploadBox.ondragover=e=>{e.preventDefault();uploadBox.classList.add(\'dragover\')};uploadBox.ondragleave=()=>uploadBox.classList.remove(\'dragover\');uploadBox.ondrop=e=>{e.preventDefault();uploadBox.classList.remove(\'dragover\');if(e.dataTransfer.files.length)analyzeFile(e.dataTransfer.files[0])};fileInput.onchange=()=>{if(fileInput.files.length)analyzeFile(fileInput.files[0])};document.addEventListener(\'paste\',e=>{for(const item of (e.clipboardData?e.clipboardData.items:[])){if(item.type&&item.type.startsWith(\'image/\')){const f=item.getAsFile();if(f){e.preventDefault();analyzeFile(f)}break}}});async function analyzeFile(file){if(!file){showError(\'붙여넣은 이미지가 없습니다.\');return}const fd=new FormData();fd.append(\'image\',file,file.name||\'clipboard.png\');setLoading(true);hideError();try{const res=await fetch(\'/api/analyze\',{method:\'POST\',body:fd});const text=await res.text();let data=null;try{data=text?JSON.parse(text):null}catch(e){throw new Error(\'서버 응답을 읽지 못했습니다. HTTP \'+res.status+(text?\' · \'+text.slice(0,180):\' · 빈 응답\'))}if(!res.ok)throw new Error((data&&data.error)||(\'분석 요청 실패 (HTTP \'+res.status+\')\'));if(!data||!data.ok)throw new Error((data&&data.error)||\'분석 실패\');renderResult(data.result)}catch(err){showError(err.message||String(err))}finally{setLoading(false)}}function setLoading(v){loading.style.display=v?\'block\':\'none\'}function hideError(){errorBox.style.display=\'none\';errorBox.textContent=\'\'}function showError(m){errorBox.textContent=m;errorBox.style.display=\'block\'}function renderResult(r){currentResult=r;document.getElementById(\'result\').style.display=\'block\';document.getElementById(\'bestCount\').textContent=r.best_count+\'방\';document.getElementById(\'bestStart\').textContent=r.best_count>0?\'1단계 \'+r.best_start+\'번 방\':\'-\';document.getElementById(\'finalRoom\').textContent=r.best_count>0?\'10단계 \'+r.final_room+\'번 방\':\'-\';document.getElementById(\'sameCount\').textContent=\'동일한 \'+r.best_count+\'방 루트: \'+r.equal_route_count+\'개\'+(r.equal_route_truncated?\' (최대 \'+r.equal_route_limit+\'개 표시)\':\'\');const starts=document.getElementById(\'starts\');starts.innerHTML=\'\';r.starts.forEach(i=>{const row=document.createElement(\'div\');row.className=\'start-row\'+(i.is_best?\' best\':\'\');row.innerHTML=\'<span>1단계 \'+i.start+\'번</span><span>\'+(i.reachable?i.count+\'방\':\'10단계 도달 불가\')+\'</span>\';starts.appendChild(row)});renderRoutes(r.routes||[])}function renderRoutes(routes){const tabs=document.getElementById(\'routeTabs\');tabs.innerHTML=\'\';routes.forEach((r,i)=>{const b=document.createElement(\'button\');b.className=\'route-tab\'+(i===0?\' active\':\'\');b.textContent=\'루트\'+(i+1)+\' 보기\';b.onclick=()=>showRoute(i);tabs.appendChild(b)});if(routes.length)showRoute(0);else{document.getElementById(\'routeMeta\').textContent=\'\';document.getElementById(\'routeImage\').removeAttribute(\'src\')}}function showRoute(i){if(!currentResult||!currentResult.routes[i])return;const r=currentResult.routes[i];document.getElementById(\'routeMeta\').innerHTML=\'시작: <strong>1단계 \'+r.start+\'번</strong> · 도착: <strong>10단계 \'+r.final_room+\'번</strong> · <strong>\'+r.count+\'방</strong>\';document.getElementById(\'routeImage\').src=\'data:image/png;base64,\'+r.image;document.querySelectorAll(\'.route-tab\').forEach((b,j)=>b.classList.toggle(\'active\',j===i))}async function pollLatest(){try{const res=await fetch(\'/api/latest/\'+encodeURIComponent(getClientCode())+\'?after=\'+currentRevision,{cache:\'no-store\'}),d=await res.json();if(d.ok&&d.changed&&d.result){currentRevision=d.revision;renderResult(d.result);hideError()}}catch(e){}}setInterval(pollLatest,700);pollLatest();\n</script></body></html>'
MAX_EQUAL_ROUTES = 30
DOT_S_MAX = 90
DOT_V_MIN = 80
DOT_V_MAX = 225
CORRIDOR_RATIO = 0.055
HORIZONTAL_MIN_RUNS = 2
VERTICAL_MIN_RUNS = 3
DIAGONAL_MIN_RUNS = 4
MAX_RUN_T_LENGTH = 0.085
ANALYZE_LOCK = threading.Lock()
LATEST_LOCK = threading.Lock()
LATEST_RESULTS = {}

# ============================================================
# 이미지 읽기
# ============================================================

def load_image(data):
    arr = np.frombuffer(data, np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("이미지를 읽을 수 없습니다.")

    return image


# ============================================================
# 50개 방 위치 자동 검출
# ============================================================

def find_diamond_centers(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 55, 145)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    h, w = image.shape[:2]
    points = []

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)

        if perimeter <= 0:
            continue

        poly = cv2.approxPolyDP(
            contour,
            0.035 * perimeter,
            True
        )

        if len(poly) != 4:
            continue

        if not cv2.isContourConvex(poly):
            continue

        x, y, bw, bh = cv2.boundingRect(poly)

        if bw < 14 or bh < 14:
            continue

        if bw > w * 0.18 or bh > h * 0.13:
            continue

        ratio = bw / float(bh)

        if not 0.65 <= ratio <= 1.35:
            continue

        points.append(
            (x + bw / 2.0, y + bh / 2.0)
        )

    if len(points) < 20:
        raise ValueError(
            "방 아이콘을 충분히 찾지 못했습니다."
        )

    clusters = []

    for point in points:
        chosen = None

        for cluster in clusters:
            cx = float(
                np.mean([p[0] for p in cluster])
            )
            cy = float(
                np.mean([p[1] for p in cluster])
            )

            if math.hypot(
                point[0] - cx,
                point[1] - cy
            ) <= 8:
                chosen = cluster
                break

        if chosen is None:
            clusters.append([point])
        else:
            chosen.append(point)

    centers = []

    for cluster in clusters:
        if len(cluster) < 2:
            continue

        centers.append(
            (
                float(
                    np.median(
                        [p[0] for p in cluster]
                    )
                ),
                float(
                    np.median(
                        [p[1] for p in cluster]
                    )
                )
            )
        )

    return centers


def cluster_axis(values, tolerance):
    clusters = []

    for value in sorted(values):
        chosen = None

        for cluster in clusters:
            center = float(
                np.median(cluster)
            )

            if abs(value - center) <= tolerance:
                chosen = cluster
                break

        if chosen is None:
            clusters.append([value])
        else:
            chosen.append(value)

    return [
        {
            "value": float(
                np.median(cluster)
            ),
            "count": len(cluster)
        }
        for cluster in clusters
    ]


def detect_room_grid(image):
    centers = find_diamond_centers(image)

    xs = [p[0] for p in centers]
    ys = [p[1] for p in centers]

    # 10행
    y_clusters = cluster_axis(ys, 9)

    y_clusters = [
        c for c in y_clusters
        if c["count"] >= 3
    ]

    if len(y_clusters) < 10:
        raise ValueError(
            "10개의 단계 위치를 찾지 못했습니다."
        )

    best_y = None

    for combo in combinations(
        y_clusters,
        10
    ):
        values = sorted(
            [c["value"] for c in combo]
        )

        gaps = np.diff(values)
        gap = float(np.median(gaps))

        if gap <= 0:
            continue

        error = float(
            np.mean(
                np.abs(gaps - gap)
            )
        )

        strength = sum(
            c["count"] for c in combo
        )

        score = error - strength * 0.15

        if (
            best_y is None
            or score < best_y["score"]
        ):
            best_y = {
                "values": values,
                "gap": gap,
                "score": score
            }

    if best_y is None:
        raise ValueError(
            "10단계 위치 계산 실패"
        )

    row_gap = best_y["gap"]

    first_y = float(
        np.median(
            [
                best_y["values"][i]
                -
                row_gap * i
                for i in range(10)
            ]
        )
    )

    final_ys = [
        first_y + row_gap * i
        for i in range(10)
    ]

    # 5열
    x_clusters = cluster_axis(
        xs,
        max(
            7,
            row_gap * 0.20
        )
    )

    x_clusters = sorted(
        x_clusters,
        key=lambda c: c["count"],
        reverse=True
    )[:9]

    if len(x_clusters) < 5:
        raise ValueError(
            "5개의 방 열을 찾지 못했습니다."
        )

    best_x = None

    for combo in combinations(
        x_clusters,
        5
    ):
        values = sorted(
            [c["value"] for c in combo]
        )

        gaps = np.diff(values)
        gap = float(np.median(gaps))

        if gap <= 0:
            continue

        error = float(
            np.mean(
                np.abs(gaps - gap)
            )
        )

        strength = sum(
            c["count"] for c in combo
        )

        score = error - strength * 0.15

        if (
            best_x is None
            or score < best_x["score"]
        ):
            best_x = {
                "values": values,
                "gap": gap,
                "score": score
            }

    if best_x is None:
        raise ValueError(
            "5열 위치 계산 실패"
        )

    column_gap = best_x["gap"]

    first_x = float(
        np.median(
            [
                best_x["values"][i]
                -
                column_gap * i
                for i in range(5)
            ]
        )
    )

    final_xs = [
        first_x + column_gap * i
        for i in range(5)
    ]

    rooms = {}

    for stage in range(10):
        for room in range(5):
            rooms[
                (stage, room)
            ] = (
                int(
                    round(
                        final_xs[room]
                    )
                ),
                int(
                    round(
                        final_ys[stage]
                    )
                )
            )

    return (
        rooms,
        column_gap,
        row_gap
    )


# ============================================================
# 점선 프로파일
# ============================================================

def build_dot_mask(image):
    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    s = hsv[:, :, 1]
    v = hsv[:, :, 2]

    mask = (
        (s <= DOT_S_MAX)
        &
        (v >= DOT_V_MIN)
        &
        (v <= DOT_V_MAX)
    )

    return mask.astype(
        np.uint8
    )


def perpendicular_vector(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    length = math.hypot(
        dx,
        dy
    )

    if length == 0:
        return 0.0, 0.0

    return (
        -dy / length,
        dx / length
    )


def make_line_profile(
    mask,
    p1,
    p2,
    spacing,
    samples=180
):
    """
    방 아이콘 자체를 제외하기 위해
    후보 선의 중앙 56%만 검사한다.

    실제 점선:
      점 / 공백 / 점 / 공백 / 점 ...

    교차하는 다른 선:
      짧은 덩어리 1~2개만 나타남
    """

    h, w = mask.shape

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    nx, ny = perpendicular_vector(
        p1,
        p2
    )

    corridor = max(
        2,
        int(
            round(
                spacing
                *
                CORRIDOR_RATIO
            )
        )
    )

    t_values = np.linspace(
        0.22,
        0.78,
        samples
    )

    profile = []

    for t in t_values:
        cx = p1[0] + dx * t
        cy = p1[1] + dy * t

        hit = False

        for offset in range(
            -corridor,
            corridor + 1
        ):
            x = int(
                round(
                    cx
                    +
                    nx * offset
                )
            )

            y = int(
                round(
                    cy
                    +
                    ny * offset
                )
            )

            if (
                0 <= x < w
                and
                0 <= y < h
                and
                mask[y, x] > 0
            ):
                hit = True
                break

        profile.append(
            1 if hit else 0
        )

    return (
        np.asarray(
            profile,
            dtype=np.uint8
        ),
        t_values
    )


def count_periodic_runs(
    profile,
    t_values
):
    padded = np.concatenate(
        (
            np.array([0], dtype=np.uint8),
            profile,
            np.array([0], dtype=np.uint8)
        )
    )

    diff = np.diff(
        padded.astype(
            np.int16
        )
    )

    starts = np.where(
        diff == 1
    )[0]

    ends = np.where(
        diff == -1
    )[0]

    runs = []

    for start, end in zip(
        starts,
        ends
    ):
        length_samples = (
            end - start
        )

        if length_samples < 2:
            continue

        start_index = min(
            start,
            len(t_values) - 1
        )

        end_index = min(
            max(
                start,
                end - 1
            ),
            len(t_values) - 1
        )

        t_start = float(
            t_values[
                start_index
            ]
        )

        t_end = float(
            t_values[
                end_index
            ]
        )

        t_length = (
            t_end
            -
            t_start
        )

        # 너무 긴 덩어리는
        # 아이콘 테두리 / 배경 UI / 교차 선이므로 제외
        if t_length > MAX_RUN_T_LENGTH:
            continue

        runs.append(
            (
                t_start,
                t_end
            )
        )

    # 매우 가까운 run은 하나의 점이 분리된 것으로 보고 합친다.
    merged = []

    for run in runs:
        if not merged:
            merged.append(
                list(run)
            )
            continue

        gap = (
            run[0]
            -
            merged[-1][1]
        )

        if gap < 0.018:
            merged[-1][1] = (
                run[1]
            )
        else:
            merged.append(
                list(run)
            )

    return merged


def analyze_connection(
    mask,
    p1,
    p2,
    spacing,
    kind
):
    profile, t_values = (
        make_line_profile(
            mask,
            p1,
            p2,
            spacing
        )
    )

    runs = count_periodic_runs(
        profile,
        t_values
    )

    run_count = len(runs)

    if kind == "horizontal":
        minimum = (
            HORIZONTAL_MIN_RUNS
        )

    elif kind == "vertical":
        minimum = (
            VERTICAL_MIN_RUNS
        )

    else:
        minimum = (
            DIAGONAL_MIN_RUNS
        )

    connected = (
        run_count >= minimum
    )

    return {
        "connected": connected,
        "runs": run_count,
        "segments": runs
    }


# ============================================================
# 그래프 생성
# ============================================================

def build_graph(image):
    (
        rooms,
        column_gap,
        row_gap
    ) = detect_room_grid(
        image
    )

    spacing = float(
        (
            column_gap
            +
            row_gap
        )
        /
        2
    )

    mask = build_dot_mask(
        image
    )

    horizontal_graph = {}
    down_graph = {}

    for stage in range(10):
        for room in range(5):
            node = (
                stage,
                room
            )

            horizontal_graph[
                node
            ] = []

            down_graph[
                node
            ] = []

    horizontal_edges = []
    vertical_edges = []
    diagonal_edges = []
    edge_details = []

    # 같은 단계 가로
    for stage in range(10):
        for room in range(4):
            a = (
                stage,
                room
            )

            b = (
                stage,
                room + 1
            )

            result = analyze_connection(
                mask,
                rooms[a],
                rooms[b],
                spacing,
                "horizontal"
            )

            edge_details.append({
                "label":
                    f"{stage + 1}단계 "
                    f"{room + 1}↔{room + 2}",
                "kind": "가로",
                "runs": result["runs"],
                "connected":
                    result["connected"]
            })

            if result["connected"]:
                horizontal_graph[
                    a
                ].append(
                    b
                )

                horizontal_graph[
                    b
                ].append(
                    a
                )

                horizontal_edges.append(
                    (a, b)
                )

    # 다음 단계
    for stage in range(9):
        for room in range(5):
            current = (
                stage,
                room
            )

            # 왼쪽 대각선
            if room > 0:
                target = (
                    stage + 1,
                    room - 1
                )

                result = analyze_connection(
                    mask,
                    rooms[current],
                    rooms[target],
                    spacing,
                    "diagonal"
                )

                edge_details.append({
                    "label":
                        f"{stage + 1}단계 "
                        f"{room + 1} → "
                        f"{stage + 2}단계 "
                        f"{room}",
                    "kind": "대각선",
                    "runs":
                        result["runs"],
                    "connected":
                        result["connected"]
                })

                if result["connected"]:
                    down_graph[
                        current
                    ].append(
                        target
                    )

                    diagonal_edges.append(
                        (
                            current,
                            target
                        )
                    )

            # 수직
            target = (
                stage + 1,
                room
            )

            result = analyze_connection(
                mask,
                rooms[current],
                rooms[target],
                spacing,
                "vertical"
            )

            edge_details.append({
                "label":
                    f"{stage + 1}단계 "
                    f"{room + 1} → "
                    f"{stage + 2}단계 "
                    f"{room + 1}",
                "kind": "수직",
                "runs":
                    result["runs"],
                "connected":
                    result["connected"]
            })

            if result["connected"]:
                down_graph[
                    current
                ].append(
                    target
                )

                vertical_edges.append(
                    (
                        current,
                        target
                    )
                )

            # 오른쪽 대각선
            if room < 4:
                target = (
                    stage + 1,
                    room + 1
                )

                result = analyze_connection(
                    mask,
                    rooms[current],
                    rooms[target],
                    spacing,
                    "diagonal"
                )

                edge_details.append({
                    "label":
                        f"{stage + 1}단계 "
                        f"{room + 1} → "
                        f"{stage + 2}단계 "
                        f"{room + 2}",
                    "kind": "대각선",
                    "runs":
                        result["runs"],
                    "connected":
                        result["connected"]
                })

                if result["connected"]:
                    down_graph[
                        current
                    ].append(
                        target
                    )

                    diagonal_edges.append(
                        (
                            current,
                            target
                        )
                    )

    return (
        horizontal_graph,
        down_graph,
        rooms,
        horizontal_edges,
        vertical_edges,
        diagonal_edges,
        edge_details
    )


# ============================================================
# 최장 경로 + 동일 최대 루트 수집
# ============================================================

def node_bit(node):
    stage, room = node

    return (
        stage * 5
        +
        room
    )


def get_valid_options(
    horizontal_graph,
    down_graph,
    node,
    visited_mask
):
    stage, _ = node

    options = []

    # 같은 단계 이동
    for next_node in horizontal_graph[node]:
        bit = node_bit(
            next_node
        )

        if (
            visited_mask
            &
            (
                1 << bit
            )
        ):
            continue

        options.append(
            next_node
        )

    # 다음 단계 이동
    if stage < 9:
        for next_node in down_graph[node]:
            bit = node_bit(
                next_node
            )

            if (
                visited_mask
                &
                (
                    1 << bit
                )
            ):
                continue

            options.append(
                next_node
            )

    return options


def find_best_routes_from_start(
    horizontal_graph,
    down_graph,
    start,
    route_limit=MAX_EQUAL_ROUTES
):
    """
    한 시작방에서 10단계까지 도달하는 경로 중
    최대 방문 방 수를 먼저 DP로 계산한 뒤,
    그 최대값과 정확히 같은 경로만 여러 개 수집한다.

    route_limit은 동일 최적 루트가 지나치게 많을 경우
    메모리 폭증을 막기 위한 표시 한도다.
    """

    @lru_cache(maxsize=None)
    def best_length(
        node,
        visited_mask
    ):
        stage, _ = node

        # 10단계 도착 자체는 유효하다.
        best = (
            1
            if stage == 9
            else None
        )

        options = get_valid_options(
            horizontal_graph,
            down_graph,
            node,
            visited_mask
        )

        for next_node in options:
            next_mask = (
                visited_mask
                |
                (
                    1
                    <<
                    node_bit(
                        next_node
                    )
                )
            )

            child_length = best_length(
                next_node,
                next_mask
            )

            if child_length is None:
                continue

            candidate = (
                1
                +
                child_length
            )

            if (
                best is None
                or
                candidate > best
            ):
                best = candidate

        return best

    initial_mask = (
        1
        <<
        node_bit(
            start
        )
    )

    maximum = best_length(
        start,
        initial_mask
    )

    if maximum is None:
        return None

    routes = []
    seen = set()
    truncated = False

    def collect(
        node,
        visited_mask,
        path
    ):
        nonlocal truncated

        if len(routes) >= route_limit:
            truncated = True
            return

        target_length = best_length(
            node,
            visited_mask
        )

        if target_length is None:
            return

        stage, _ = node

        # 이 상태에서 현재 방 하나만으로 최적 길이를 달성하면
        # 즉 10단계 종료가 최적이면 경로 하나 완성.
        if (
            stage == 9
            and
            target_length == 1
        ):
            key = tuple(path)

            if key not in seen:
                seen.add(key)
                routes.append(
                    list(path)
                )

            return

        options = get_valid_options(
            horizontal_graph,
            down_graph,
            node,
            visited_mask
        )

        for next_node in options:
            next_mask = (
                visited_mask
                |
                (
                    1
                    <<
                    node_bit(
                        next_node
                    )
                )
            )

            child_length = best_length(
                next_node,
                next_mask
            )

            if child_length is None:
                continue

            # 최적 경로에 포함되는 branch만 따라간다.
            if (
                1
                +
                child_length
                !=
                target_length
            ):
                continue

            collect(
                next_node,
                next_mask,
                path
                +
                [next_node]
            )

            if len(routes) >= route_limit:
                truncated = True
                return

    collect(
        start,
        initial_mask,
        [start]
    )

    return {
        "count":
            maximum,
        "routes":
            routes,
        "truncated":
            truncated
    }


def calculate_all_starts(
    horizontal_graph,
    down_graph
):
    results = []

    for room in range(5):
        start = (
            0,
            room
        )

        result = find_best_routes_from_start(
            horizontal_graph,
            down_graph,
            start,
            route_limit=MAX_EQUAL_ROUTES
        )

        if result is None:
            results.append({
                "start":
                    room + 1,
                "reachable":
                    False,
                "count":
                    0,
                "route":
                    [],
                "routes":
                    [],
                "truncated":
                    False,
                "is_best":
                    False
            })

        else:
            first_route = (
                result["routes"][0]
                if result["routes"]
                else []
            )

            results.append({
                "start":
                    room + 1,
                "reachable":
                    True,
                "count":
                    result["count"],
                "route":
                    first_route,
                "routes":
                    result["routes"],
                "truncated":
                    result["truncated"],
                "is_best":
                    False
            })

    return results


# ============================================================
# 이미지 출력
# ============================================================

def encode_image(image):
    ok, buffer = cv2.imencode(
        ".png",
        image
    )

    if not ok:
        raise ValueError(
            "결과 이미지 생성 실패"
        )

    return (
        base64.b64encode(
            buffer.tobytes()
        ).decode(
            "utf-8"
        )
    )


def drawing_scale(rooms):
    xs = sorted(
        set(
            x
            for x, y
            in rooms.values()
        )
    )

    if len(xs) >= 2:
        return abs(
            xs[1] - xs[0]
        )

    return 50


def draw_route(
    image,
    rooms,
    route
):
    output = image.copy()

    if not route:
        return output

    gap = drawing_scale(
        rooms
    )

    thickness = max(
        2,
        int(
            round(
                gap * 0.06
            )
        )
    )

    radius = max(
        9,
        int(
            round(
                gap * 0.21
            )
        )
    )

    for i in range(
        len(route) - 1
    ):
        cv2.arrowedLine(
            output,
            rooms[
                route[i]
            ],
            rooms[
                route[i + 1]
            ],
            (0, 0, 255),
            thickness,
            cv2.LINE_AA,
            tipLength=0.16
        )

    for order, node in enumerate(
        route,
        start=1
    ):
        x, y = rooms[node]

        cv2.circle(
            output,
            (x, y),
            radius + 2,
            (15, 15, 15),
            -1
        )

        cv2.circle(
            output,
            (x, y),
            radius,
            (30, 60, 240),
            -1
        )

        text = str(
            order
        )

        font_scale = max(
            0.35,
            gap / 125.0
        )

        (
            tw,
            th
        ), _ = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            1
        )

        cv2.putText(
            output,
            text,
            (
                x - tw // 2,
                y + th // 2
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

    return output


def draw_debug_edges(
    image,
    rooms,
    horizontal_edges,
    vertical_edges,
    diagonal_edges
):
    output = image.copy()

    gap = drawing_scale(
        rooms
    )

    thickness = max(
        2,
        int(
            round(
                gap * 0.045
            )
        )
    )

    # 가로 = 초록
    for a, b in horizontal_edges:
        cv2.line(
            output,
            rooms[a],
            rooms[b],
            (0, 220, 0),
            thickness,
            cv2.LINE_AA
        )

    # 수직 = 파랑
    for a, b in vertical_edges:
        cv2.line(
            output,
            rooms[a],
            rooms[b],
            (255, 80, 0),
            thickness,
            cv2.LINE_AA
        )

    # 대각선 = 청록
    for a, b in diagonal_edges:
        cv2.line(
            output,
            rooms[a],
            rooms[b],
            (255, 180, 0),
            thickness,
            cv2.LINE_AA
        )

    return output


# ============================================================
# 결과 생성
# ============================================================

def route_to_web_data(
    image,
    rooms,
    route,
    start_room
):
    """
    화면 전환에 필요한 최소 데이터만 만든다.
    이동 순서/디버그 표시는 제거했으므로
    이미지 + 시작/도착/방 수만 반환한다.
    """
    route_image = draw_route(
        image,
        rooms,
        route
    )

    return {
        "start":
            start_room,
        "final_room":
            route[-1][1] + 1,
        "count":
            len(route),
        "image":
            encode_image(
                route_image
            )
    }


def make_result(
    image,
    horizontal_graph,
    down_graph,
    rooms,
    horizontal_edges,
    vertical_edges,
    diagonal_edges,
    edge_details
):
    starts = calculate_all_starts(
        horizontal_graph,
        down_graph
    )

    reachable = [
        item
        for item in starts
        if item["reachable"]
    ]

    if not reachable:
        return {
            "best_count":
                0,
            "best_start":
                "-",
            "final_room":
                "-",
            "starts":
                starts,
            "route":
                [],
            "route_summary":
                "",
            "route_image":
                encode_image(
                    image
                ),
            "routes":
                [],
            "equal_route_count":
                0,
            "equal_route_truncated":
                False,
            "equal_route_limit":
                MAX_EQUAL_ROUTES,
        }

    best_count = max(
        item["count"]
        for item in reachable
    )

    for item in starts:
        item["is_best"] = (
            item["reachable"]
            and
            item["count"]
            ==
            best_count
        )

    # --------------------------------------------------------
    # 모든 시작점에서 '전역 최대 방 수'와 같은 루트만 모은다.
    # --------------------------------------------------------

    equal_routes = []
    seen = set()
    truncated = False

    for item in starts:
        if (
            not item["reachable"]
            or
            item["count"]
            !=
            best_count
        ):
            continue

        for route in item["routes"]:
            key = tuple(
                route
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            equal_routes.append(
                {
                    "start":
                        item["start"],
                    "route":
                        route
                }
            )

            if (
                len(equal_routes)
                >=
                MAX_EQUAL_ROUTES
            ):
                truncated = True
                break

        if item["truncated"]:
            truncated = True

        if (
            len(equal_routes)
            >=
            MAX_EQUAL_ROUTES
        ):
            break

    # DP상 최대경로가 있는데 수집 한도 문제로 비었다면
    # 각 시작점의 첫 경로를 fallback으로 사용.
    if not equal_routes:
        for item in starts:
            if (
                item["reachable"]
                and
                item["count"]
                ==
                best_count
                and
                item["route"]
            ):
                equal_routes.append({
                    "start":
                        item["start"],
                    "route":
                        item["route"]
                })

                break

    route_views = []

    for item in equal_routes:
        route_views.append(
            route_to_web_data(
                image,
                rooms,
                item["route"],
                item["start"]
            )
        )

    first = route_views[0]

    return {
        "best_count":
            best_count,
        "best_start":
            first["start"],
        "final_room":
            first["final_room"],
        "starts":
            starts,
        "route":
            [],
        "route_summary":
            "",
        "route_image":
            first["image"],
        "routes":
            route_views,
        "equal_route_count":
            len(route_views),
        "equal_route_truncated":
            truncated,
        "equal_route_limit":
            MAX_EQUAL_ROUTES,
    }


# ============================================================
# 적응형 분석
# ============================================================

def analyze_with_thresholds(
    image,
    horizontal_runs,
    vertical_runs,
    diagonal_runs,
    mode_name
):
    """
    동일 이미지를 서로 다른 점선 민감도로 분석한다.

    strict:
      기존에 잘 맞던 샘플의 오검출을 최소화.

    relaxed:
      strict에서 10단계 경로 자체가 끊긴 경우에만 사용.
      한 단계 낮은 반복점 기준으로 실제 점선 누락을 복구한다.
    """
    global HORIZONTAL_MIN_RUNS
    global VERTICAL_MIN_RUNS
    global DIAGONAL_MIN_RUNS

    old_h = HORIZONTAL_MIN_RUNS
    old_v = VERTICAL_MIN_RUNS
    old_d = DIAGONAL_MIN_RUNS

    try:
        HORIZONTAL_MIN_RUNS = horizontal_runs
        VERTICAL_MIN_RUNS = vertical_runs
        DIAGONAL_MIN_RUNS = diagonal_runs

        (
            horizontal_graph,
            down_graph,
            rooms,
            horizontal_edges,
            vertical_edges,
            diagonal_edges,
            edge_details
        ) = build_graph(image)

        result = make_result(
            image,
            horizontal_graph,
            down_graph,
            rooms,
            horizontal_edges,
            vertical_edges,
            diagonal_edges,
            edge_details
        )

        result["mode"] = mode_name

        return result

    finally:
        HORIZONTAL_MIN_RUNS = old_h
        VERTICAL_MIN_RUNS = old_v
        DIAGONAL_MIN_RUNS = old_d


def adaptive_analyze(image):
    """
    1차 정밀 분석에서 경로가 나오면 그대로 사용.
    실패한 경우에만 보정 분석을 한 번 더 수행한다.
    """
    strict_result = analyze_with_thresholds(
        image,
        horizontal_runs=2,
        vertical_runs=3,
        diagonal_runs=4,
        mode_name="정밀"
    )

    if strict_result["best_count"] > 0:
        return strict_result

    return analyze_with_thresholds(
        image,
        horizontal_runs=2,
        vertical_runs=2,
        diagonal_runs=3,
        mode_name="보정"
    )






def safe_analyze(image):
    with ANALYZE_LOCK:
        return adaptive_analyze(image)

def compact_result(result):
    return {
        "best_count": result["best_count"],
        "best_start": result["best_start"],
        "final_room": result["final_room"],
        "starts": [{"start": i["start"], "reachable": i["reachable"], "count": i["count"], "is_best": i["is_best"]} for i in result["starts"]],
        "routes": result.get("routes", []),
        "equal_route_count": result.get("equal_route_count", 0),
        "equal_route_truncated": result.get("equal_route_truncated", False),
        "equal_route_limit": result.get("equal_route_limit", MAX_EQUAL_ROUTES),
        "mode": result.get("mode", ""),
    }

def prune_old_results():
    cutoff = time.time() - 10800
    with LATEST_LOCK:
        for key in [k for k,v in LATEST_RESULTS.items() if v.get("updated_at",0) < cutoff]:
            LATEST_RESULTS.pop(key,None)

def analyze_uploaded_file(file_storage):
    if not file_storage:
        raise ValueError("이미지가 없습니다.")
    data=file_storage.read()
    if not data:
        raise ValueError("이미지가 비어 있습니다.")
    return compact_result(safe_analyze(load_image(data)))

@app.get("/")
def web_home():
    return WEB_HTML

@app.get('/health')
def health():
    return jsonify(ok=True, version=APP_VERSION)

@app.post('/api/analyze')
def analyze():
    try:
        if 'image' not in request.files:
            return jsonify(ok=False,error='image 파일이 없습니다.'),400
        return jsonify(ok=True,result=analyze_uploaded_file(request.files['image']))
    except Exception as exc:
        return jsonify(ok=False,error=str(exc)),400

@app.post('/api/analyze-client/<client_id>')
def analyze_client(client_id):
    try:
        if not client_id or len(client_id)>100:
            return jsonify(ok=False,error='잘못된 연결 코드입니다.'),400
        if 'image' not in request.files:
            return jsonify(ok=False,error='image 파일이 없습니다.'),400
        result=analyze_uploaded_file(request.files['image'])
        now=time.time()
        with LATEST_LOCK:
            prev=LATEST_RESULTS.get(client_id,{})
            revision=int(prev.get('revision',0))+1
            LATEST_RESULTS[client_id]={'revision':revision,'result':result,'updated_at':now}
        prune_old_results()
        return jsonify(ok=True,revision=revision,result=result)
    except Exception as exc:
        return jsonify(ok=False,error=str(exc)),400

@app.get('/api/latest/<client_id>')
def latest(client_id):
    try: after=int(request.args.get('after','0'))
    except ValueError: after=0
    with LATEST_LOCK:
        item=LATEST_RESULTS.get(client_id)
        if not item:
            return jsonify(ok=True,changed=False,revision=0)
        revision=int(item['revision'])
        if revision<=after:
            return jsonify(ok=True,changed=False,revision=revision)
        return jsonify(ok=True,changed=True,revision=revision,result=item['result'])

if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000,debug=False,use_reloader=False)